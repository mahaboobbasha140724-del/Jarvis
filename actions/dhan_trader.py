"""
dhan_trader.py — Dhan Brokerage API integration for JARVIS
Official Dhan API: https://dhanhq.co/docs/v2/
Install: pip install dhanhq

Supports:
  - buy / sell (market or limit orders)
  - portfolio (current positions)
  - holdings (long-term CNC holdings)
  - order_status (check order)
  - market_quote (live NSE price)
  - order_history (today's orders)
"""

import json
import sys
from pathlib import Path

def _get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

_CONFIG_PATH = _get_base_dir() / "config" / "api_keys.json"

def _load_config():
    try:
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _get_dhan_client():
    """Returns an authenticated DhanHQ client or raises ValueError."""
    try:
        from dhanhq import DhanHQ
    except ImportError:
        raise ImportError(
            "dhanhq package not installed. "
            "Run: pip install dhanhq"
        )
    cfg = _load_config()
    client_id = cfg.get("dhan_client_id", "").strip()
    access_token = cfg.get("dhan_access_token", "").strip()

    if not client_id or not access_token:
        raise ValueError(
            "Dhan Client ID and Access Token not configured. "
            "Please enter them in the JARVIS dashboard Settings panel."
        )
    return DhanHQ(client_id, access_token)


# ──────────────────────────────────────────────
#  NSE Security ID lookup (common large-caps)
#  Dhan uses numeric security_id not ticker symbols
# ──────────────────────────────────────────────
# Key: upper-case ticker → Dhan security_id (NSE EQ segment)
_NSE_SECURITY_MAP = {
    "RELIANCE":  "2885",
    "TCS":       "11536",
    "INFY":      "1594",
    "HDFCBANK":  "1333",
    "ICICIBANK": "4963",
    "HINDUNILVR":"1435",
    "SBIN":      "3045",
    "BAJFINANCE":"317",
    "BHARTIARTL":"10604",
    "WIPRO":     "3787",
    "KOTAKBANK": "1922",
    "AXISBANK":  "5900",
    "LT":        "11483",
    "ASIANPAINT":"1270",
    "MARUTI":    "10999",
    "SUNPHARMA": "3351",
    "TITAN":     "3506",
    "ADANIENT":  "25",
    "ADANIPORTS":"15083",
    "POWERGRID": "14977",
    "NESTLEIND": "17963",
    "ULTRACEMCO":"11532",
    "TECHM":     "13538",
    "HCLTECH":   "1363",
    "ONGC":      "2475",
    "NTPC":      "2474",
    "COALINDIA": "20374",
    "JSWSTEEL":  "11723",
    "TATASTEEL": "3499",
    "TATAMOTORS":"3456",
    "M&M":       "2031",
    "GRASIM":    "1232",
    "CIPLA":     "1080",
    "DIVISLAB":  "10940",
    "DRREDDY":   "881",
    "EICHERMOT": "910",
    "UPL":       "11287",
    "BPCL":      "526",
    "INDUSINDBK":"5258",
    "BAJAJFINSV":"16675",
    "BAJAJ-AUTO":"317",
    "BRITANNIA": "547",
    "HEROMOTOCO":"1348",
    "ITC":       "1660",
    "HDFCLIFE":  "119",
    "SBILIFE":   "21808",
    "APOLLOHOSP":"157",
}

def _resolve_security_id(symbol: str) -> tuple[str, str]:
    """
    Returns (security_id, exchange_segment).
    Tries _NSE_SECURITY_MAP first, falls back to live search.
    """
    sym = symbol.strip().upper().replace(" ", "")
    if sym in _NSE_SECURITY_MAP:
        return _NSE_SECURITY_MAP[sym], "NSE_EQ"
    # If user gave a numeric ID directly
    if sym.isdigit():
        return sym, "NSE_EQ"
    raise ValueError(
        f"Could not find security ID for '{symbol}'. "
        f"Please use exact NSE ticker (e.g. RELIANCE, TCS, INFY). "
        f"Supported list: {', '.join(list(_NSE_SECURITY_MAP.keys())[:20])}..."
    )


def dhan_trader(parameters=None, player=None, **kwargs):
    """
    Main entry for all Dhan trading actions.
    parameters keys:
        action        (str) — buy | sell | portfolio | holdings |
                               order_status | market_quote | order_history
        symbol        (str) — Stock ticker e.g. RELIANCE, TCS
        quantity      (int) — Number of shares
        order_type    (str) — MARKET | LIMIT (default: MARKET)
        price         (float) — Limit price (required for LIMIT orders)
        product_type  (str) — CNC (delivery) | INTRADAY / MIS (default: CNC)
        order_id      (str) — For order_status action
        confirm       (bool) — Must be True to execute buy/sell (safety gate)
    """
    if isinstance(parameters, str):
        parameters = {"action": parameters}
    if not isinstance(parameters, dict):
        return "Error: No parameters provided."

    action       = parameters.get("action", "portfolio").lower().strip()
    symbol       = parameters.get("symbol", "").strip().upper()
    quantity     = int(parameters.get("quantity", 1))
    order_type   = parameters.get("order_type", "MARKET").upper()
    price        = float(parameters.get("price", 0.0))
    product_type = parameters.get("product_type", "CNC").upper()
    order_id     = parameters.get("order_id", "").strip()
    confirm      = parameters.get("confirm", False)

    # Normalize product type
    if product_type in ("INTRADAY", "MIS"):
        product_type = "INTRADAY"
    else:
        product_type = "CNC"

    log = lambda msg: (print(msg), player.write_log(msg) if player else None)

    try:
        dhan = _get_dhan_client()
    except (ImportError, ValueError) as e:
        return f"[Dhan] Error: {e}"
    except Exception as e:
        return f"[Dhan] Authentication failed: {e}"

    # ── MARKET QUOTE ──
    if action == "market_quote":
        if not symbol:
            return "Please provide a stock symbol (e.g. RELIANCE, TCS)."
        try:
            sec_id, exchange = _resolve_security_id(symbol)
            log(f"[Dhan] Fetching live quote for {symbol}...")
            resp = dhan.get_market_feed_scrip(exchange, sec_id)
            data = resp.get("data", {})
            ltp  = data.get("LTP") or data.get("last_price", "N/A")
            high = data.get("DayHigh", "N/A")
            low  = data.get("DayLow", "N/A")
            open_= data.get("DayOpen", "N/A")
            chg  = data.get("change", "N/A")
            chgp = data.get("change_per", "N/A")
            return (
                f"[Dhan] {symbol} Live Quote:\n"
                f"  Last Price : ₹{ltp}\n"
                f"  Open       : ₹{open_}\n"
                f"  Day High   : ₹{high}\n"
                f"  Day Low    : ₹{low}\n"
                f"  Change     : {chg} ({chgp}%)"
            )
        except Exception as e:
            return f"[Dhan] Quote error: {e}"

    # ── PORTFOLIO / POSITIONS ──
    if action in ("portfolio", "positions"):
        try:
            log("[Dhan] Fetching open positions...")
            resp = dhan.get_positions()
            positions = resp.get("data", []) if isinstance(resp, dict) else (resp or [])
            if not positions:
                return "[Dhan] No open positions currently."
            lines = ["[Dhan] Open Positions:"]
            total_pnl = 0.0
            for p in positions:
                sym   = p.get("tradingSymbol", p.get("symbol", "?"))
                qty   = p.get("netQty", p.get("quantity", 0))
                avg   = p.get("averageTradedPrice", p.get("avgPrice", 0))
                ltp   = p.get("lastTradedPrice", p.get("ltp", 0))
                pnl   = p.get("realizedProfit", 0) + p.get("unrealizedProfit", 0)
                total_pnl += float(pnl) if pnl else 0
                lines.append(
                    f"  {sym:15s} Qty:{qty:5}  Avg:₹{avg:.2f}  LTP:₹{ltp:.2f}  P&L:₹{pnl:.2f}"
                )
            lines.append(f"\n  Total P&L: ₹{total_pnl:.2f}")
            return "\n".join(lines)
        except Exception as e:
            return f"[Dhan] Portfolio error: {e}"

    # ── HOLDINGS (long-term CNC) ──
    if action == "holdings":
        try:
            log("[Dhan] Fetching holdings...")
            resp = dhan.get_holdings()
            holdings = resp.get("data", []) if isinstance(resp, dict) else (resp or [])
            if not holdings:
                return "[Dhan] No holdings found."
            lines = ["[Dhan] Holdings (CNC):"]
            total_value = 0.0
            for h in holdings:
                sym   = h.get("tradingSymbol", h.get("symbol", "?"))
                qty   = h.get("totalQty", h.get("quantity", 0))
                avg   = h.get("avgCostPrice", h.get("avgPrice", 0))
                ltp   = h.get("lastTradedPrice", h.get("ltp", 0))
                value = float(qty) * float(ltp) if qty and ltp else 0
                total_value += value
                pnl   = (float(ltp) - float(avg)) * float(qty) if avg and ltp and qty else 0
                lines.append(
                    f"  {sym:15s} Qty:{qty:5}  Avg:₹{avg:.2f}  LTP:₹{ltp:.2f}  "
                    f"Value:₹{value:.0f}  P&L:₹{pnl:.0f}"
                )
            lines.append(f"\n  Total Portfolio Value: ₹{total_value:.0f}")
            return "\n".join(lines)
        except Exception as e:
            return f"[Dhan] Holdings error: {e}"

    # ── ORDER HISTORY ──
    if action == "order_history":
        try:
            log("[Dhan] Fetching today's orders...")
            resp = dhan.get_order_list()
            orders = resp.get("data", []) if isinstance(resp, dict) else (resp or [])
            if not orders:
                return "[Dhan] No orders today."
            lines = ["[Dhan] Today's Orders:"]
            for o in orders[:10]:
                sym    = o.get("tradingSymbol", "?")
                otype  = o.get("transactionType", "?")
                qty    = o.get("quantity", 0)
                price_ = o.get("price", 0)
                status = o.get("orderStatus", "?")
                oid    = o.get("orderId", "?")
                lines.append(
                    f"  [{status}] {otype} {sym} x{qty} @ ₹{price_}  (ID: {oid})"
                )
            return "\n".join(lines)
        except Exception as e:
            return f"[Dhan] Order history error: {e}"

    # ── ORDER STATUS ──
    if action == "order_status":
        if not order_id:
            return "Please provide an order_id to check status."
        try:
            resp = dhan.get_order_by_id(order_id)
            o = resp.get("data", resp)
            return (
                f"[Dhan] Order {order_id}:\n"
                f"  Status : {o.get('orderStatus','?')}\n"
                f"  Symbol : {o.get('tradingSymbol','?')}\n"
                f"  Type   : {o.get('transactionType','?')}\n"
                f"  Qty    : {o.get('quantity','?')}\n"
                f"  Price  : ₹{o.get('price','?')}"
            )
        except Exception as e:
            return f"[Dhan] Order status error: {e}"

    # ── BUY / SELL ──
    if action in ("buy", "sell"):
        if not symbol:
            return "Please specify a stock symbol (e.g. RELIANCE, TCS, INFY)."
        if quantity <= 0:
            return "Quantity must be greater than 0."

        # SAFETY GATE — requires explicit confirm=True from AI
        if not confirm:
            # Return a confirmation request instead of executing
            direction = "BUY" if action == "buy" else "SELL"
            price_str = f"₹{price}" if order_type == "LIMIT" else "MARKET PRICE"
            return (
                f"[Dhan] ⚠️ TRADE CONFIRMATION REQUIRED\n"
                f"  Action      : {direction}\n"
                f"  Stock       : {symbol} (NSE)\n"
                f"  Quantity    : {quantity} shares\n"
                f"  Order Type  : {order_type} @ {price_str}\n"
                f"  Product     : {product_type} ({'Delivery/Long-term' if product_type=='CNC' else 'Intraday'})\n\n"
                f"Say 'Yes, confirm the trade' or 'Cancel' to proceed."
            )

        try:
            sec_id, exchange = _resolve_security_id(symbol)
            log(f"[Dhan] Placing {action.upper()} order: {quantity} x {symbol}...")

            transaction_type = "BUY" if action == "buy" else "SELL"

            order_resp = dhan.place_order(
                security_id   = sec_id,
                exchange_segment = exchange,
                transaction_type = transaction_type,
                quantity      = quantity,
                order_type    = order_type,
                product_type  = product_type,
                price         = price if order_type == "LIMIT" else 0,
            )

            order_data = order_resp.get("data", order_resp) if isinstance(order_resp, dict) else order_resp
            oid = (order_data.get("orderId") or
                   order_data.get("order_id") or
                   str(order_data))

            result = (
                f"[Dhan] ✅ {transaction_type} order placed successfully!\n"
                f"  Stock    : {symbol} (NSE)\n"
                f"  Quantity : {quantity} shares\n"
                f"  Type     : {order_type}\n"
                f"  Product  : {product_type}\n"
                f"  Order ID : {oid}\n"
                f"  Status   : Order submitted to exchange."
            )
            log(result)
            return result

        except ValueError as e:
            return f"[Dhan] Symbol error: {e}"
        except Exception as e:
            return f"[Dhan] Order placement failed: {str(e)}"

    return f"[Dhan] Unknown action '{action}'. Use: buy | sell | portfolio | holdings | market_quote | order_history | order_status"
