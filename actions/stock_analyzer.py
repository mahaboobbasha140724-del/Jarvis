"""
stock_analyzer.py — JARVIS Enhanced Stock Analyzer
Supports: US stocks, Indian NSE (.NS) and BSE (.BO) stocks
Auto-detects Indian tickers and adds appropriate suffix.
"""

import os
from pathlib import Path
import yfinance as yf
import pandas as pd
import numpy as np

# ── Indian NSE ticker set (auto-append .NS) ──
_KNOWN_NSE_TICKERS = {
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","HINDUNILVR",
    "SBIN","BAJFINANCE","BHARTIARTL","WIPRO","KOTAKBANK","AXISBANK",
    "LT","ASIANPAINT","MARUTI","SUNPHARMA","TITAN","ADANIENT",
    "ADANIPORTS","POWERGRID","NESTLEIND","ULTRACEMCO","TECHM","HCLTECH",
    "ONGC","NTPC","COALINDIA","JSWSTEEL","TATASTEEL","TATAMOTORS",
    "M&M","GRASIM","CIPLA","DIVISLAB","DRREDDY","EICHERMOT","UPL",
    "BPCL","INDUSINDBK","BAJAJFINSV","BAJAJ-AUTO","BRITANNIA","HEROMOTOCO",
    "ITC","HDFCLIFE","SBILIFE","APOLLOHOSP","NIFTY50","SENSEX","BANKNIFTY",
    "NIFTYIT","NIFTYFMCG","MIDCAP","SMALLCAP",
    # More mid-caps
    "ZOMATO","PAYTM","IRCTC","PIDILITIND","HAVELLS","BERGEPAINT",
    "MUTHOOTFIN","IRFC","RVNL","NHPC","RECLTD","PFC","HAL","BEL","BHEL",
    "TATAPOWER","ADANIGREEN","ADANITRANS","TORNTPHARM","GLAXO","PFIZER",
    "ABBOTINDIA","ALKEM","LUPIN","BIOCON","AUROPHARMA","METROPOLIS",
    "DMART","TRENT","NAUKRI","JUSTDIAL","INFOEDGE","ZYDUSLIFE",
    "GODREJCP","DABUR","MARICO","COLPAL","EMAMILTD","PIDILITIND",
    "TATACONSUM","MCDOWELL-N","RADICO","UNITDSPR","KANSAINER",
    "MOTHERSON","BALKRISIND","BOSCHLTD","EXIDEIND","AMARARAJA","MRF",
    "APOLLOTYRE","CEATLTD","TATACHEM","PIINDUSTRIES","DEEPAKNTR",
    "NAVINFLUOR","AAVAS","CANFINHOME","LICHSGFIN","PNBHOUSING",
    "IDFCFIRSTB","FEDERALBNK","RBLBANK","AUBANK","EQUITASBNK",
    "BANKBARODA","CANBK","UNIONBANK","PNB","IOB","CENTRALBK","UCO",
    "SIEMENS","ABB","CUMMINSIND","THERMAX","VOLTAS","BLUESTARCO",
    "WHIRLPOOL","DIXON","AMBER","POLYCAB","KEI","FINOLEX",
    "JUBLFOOD","WESTLIFE","DEVYANI","SAPPHIRE","BARBEQUE","ZSWEETS",
    "INDIAMART","RATEGAIN","MPHASIS","LTTS","PERSISTENT","COFORGE",
    "KPITTECH","ZENSAR","CYIENT","HEXAWARE","MASTEK","NIIT",
    "TATAELXSI","HAPPSTMNDS","SONATSOFTW","TANLA","NEWGEN",
    "PGHH","GILLETTE","3MINDIA","HONAUT","ASIANHO","JKCEMENT",
    "SHREECEM","ACC","AMBUJACEM","RAMCOCEM","DALBHARAT","HEIDELBERG",
    "EDELWEISS","MOTILALOSW","ANGELONE","5PAISA","IIFL","MANAPPURAM",
    "GOLDIAM","MMTC","NALCO","HINDALCO","VEDL","NATIONALUM","MOIL",
    "SAIL","NMDC","HINDZINC","RATNAMANI","WELCORP","TATA",
}

# Index tickers mapping
_INDEX_MAP = {
    "NIFTY50":    "^NSEI",
    "SENSEX":     "^BSESN",
    "BANKNIFTY":  "^NSEBANK",
    "NIFTYIT":    "^CNXIT",
    "NIFTYFMCG":  "^CNXFMCG",
    "MIDCAP":     "^NSEMDCP50",
    "SMALLCAP":   "^CNXSC",
    "DOWJONES":   "^DJI",
    "SP500":      "^GSPC",
    "NASDAQ":     "^IXIC",
}

def _resolve_ticker(symbol: str) -> tuple[str, str]:
    """
    Returns (yfinance_ticker, currency_symbol).
    Auto-appends .NS for Indian stocks.
    """
    sym = symbol.strip().upper()

    # Index
    if sym in _INDEX_MAP:
        return _INDEX_MAP[sym], "₹" if "NSEI" in _INDEX_MAP[sym] or "BSE" in _INDEX_MAP[sym] else "$"

    # Already has suffix
    if sym.endswith(".NS") or sym.endswith(".BO"):
        return sym, "₹"

    # Known Indian ticker → append .NS
    if sym in _KNOWN_NSE_TICKERS:
        return f"{sym}.NS", "₹"

    # Heuristic: no dots, no digits, 1-10 chars, likely Indian
    clean = sym.replace("-", "").replace("&", "")
    if clean.isalpha() and len(clean) >= 3 and clean.isupper():
        # If short symbol that looks Indian (no common US pattern), try .NS
        if len(clean) <= 8 and not clean.endswith(("X","Q","Z")):
            return f"{sym}.NS", "₹"

    # Default: treat as US ticker
    return sym, "$"


def stock_analyzer(parameters=None, player=None, **kwargs):
    """
    Analyze any stock — Indian (NSE/BSE) or US.
    parameters: dict or str with ticker symbol.
    """
    ticker_symbol = ""
    if isinstance(parameters, dict):
        ticker_symbol = parameters.get("ticker", parameters.get("symbol", "")).strip().upper()
    elif isinstance(parameters, str):
        ticker_symbol = parameters.strip().upper()

    if not ticker_symbol:
        return "Error: No ticker symbol provided. Example: RELIANCE, TCS, AAPL, GOOGL"

    print(f"[Stock Analyzer] Analyzing: {ticker_symbol}")

    # Resolve to actual yfinance ticker
    yf_symbol, currency = _resolve_ticker(ticker_symbol)
    print(f"[Stock Analyzer] Using yfinance symbol: {yf_symbol}")

    try:
        ticker = yf.Ticker(yf_symbol)
        info   = ticker.info or {}

        # Fetch history
        history = ticker.history(period="1y")
        if history.empty:
            # Try BSE if NSE failed
            if yf_symbol.endswith(".NS"):
                alt = yf_symbol.replace(".NS", ".BO")
                print(f"[Stock Analyzer] NSE failed, trying BSE: {alt}")
                ticker  = yf.Ticker(alt)
                info    = ticker.info or {}
                history = ticker.history(period="1y")
                if not history.empty:
                    currency = "₹"

            if history.empty:
                return (
                    f"Error: Could not retrieve data for '{ticker_symbol}'. "
                    f"Please check the symbol. Indian stocks: use RELIANCE, TCS, INFY etc."
                )

        # ── Fundamental Data ──
        name     = info.get("longName") or info.get("shortName") or ticker_symbol
        sector   = info.get("sector",   "N/A")
        industry = info.get("industry", "N/A")
        summary  = info.get("longBusinessSummary", "No description available.")[:500] + "..."

        price = (info.get("currentPrice")
              or info.get("regularMarketPrice")
              or (history["Close"].iloc[-1] if not history.empty else None))

        market_cap     = info.get("marketCap", 0)
        pe_ratio       = info.get("trailingPE", "N/A")
        forward_pe     = info.get("forwardPE", "N/A")
        peg_ratio      = info.get("pegRatio", "N/A")
        pb_ratio       = info.get("priceToBook", "N/A")
        debt_to_equity = info.get("debtToEquity", "N/A")
        profit_margin  = info.get("profitMargins", "N/A")
        roe            = info.get("returnOnEquity", "N/A")
        div_yield      = (info.get("dividendYield") or 0) * 100
        free_cash_flow = info.get("freeCashflow", "N/A")
        week52_high    = info.get("fiftyTwoWeekHigh", "N/A")
        week52_low     = info.get("fiftyTwoWeekLow", "N/A")
        volume         = info.get("volume", info.get("regularMarketVolume", "N/A"))
        avg_volume     = info.get("averageVolume", "N/A")

        # Format for Indian/US currency
        def fmt_price(v):
            if v is None: return "N/A"
            return f"{currency}{v:,.2f}"

        def fmt_cap(v):
            if not v: return "N/A"
            if currency == "₹":
                if v >= 1e12: return f"₹{v/1e12:.2f}T (₹{v/1e7:.0f}Cr)"
                if v >= 1e9:  return f"₹{v/1e9:.2f}B (₹{v/1e7:.0f}Cr)"
                return f"₹{v/1e7:.2f}Cr"
            else:
                if v >= 1e12: return f"${v/1e12:.2f}T"
                if v >= 1e9:  return f"${v/1e9:.2f}B"
                return f"${v/1e6:.2f}M"

        pe_str  = f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else "N/A"
        fpe_str = f"{forward_pe:.2f}" if isinstance(forward_pe, (int, float)) else "N/A"
        peg_str = f"{peg_ratio:.2f}" if isinstance(peg_ratio, (int, float)) else "N/A"
        pb_str  = f"{pb_ratio:.2f}"  if isinstance(pb_ratio, (int, float)) else "N/A"
        pm_str  = f"{profit_margin*100:.2f}%" if isinstance(profit_margin, (int, float)) else "N/A"
        roe_str = f"{roe*100:.2f}%"  if isinstance(roe, (int, float)) else "N/A"
        dy_str  = f"{div_yield:.2f}%" if div_yield else "0.00%"
        fcf_str = (f"{currency}{free_cash_flow/1e7:.2f}Cr"
                   if isinstance(free_cash_flow, (int, float)) and currency == "₹"
                   else f"${free_cash_flow/1e6:.2f}M" if isinstance(free_cash_flow, (int, float))
                   else "N/A")

        # ── Technical Indicators ──
        tech_summary = ""
        rsi = rsi_signal = trend_signal = macd_signal = None

        if not history.empty and len(history) >= 20:
            close = history["Close"]

            sma_50  = close.rolling(50).mean().iloc[-1]  if len(close) >= 50  else None
            sma_200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None

            # RSI
            delta = close.diff()
            gain  = delta.where(delta > 0, 0)
            loss  = -delta.where(delta < 0, 0)
            rs    = gain.rolling(14).mean() / (loss.rolling(14).mean() + 1e-10)
            rsi   = (100 - 100 / (1 + rs)).iloc[-1]

            if rsi > 75:   rsi_signal = "Strongly Overbought 🔴"
            elif rsi > 60: rsi_signal = "Overbought 🟠"
            elif rsi < 25: rsi_signal = "Strongly Oversold 🟢"
            elif rsi < 40: rsi_signal = "Oversold 🟡"
            else:           rsi_signal = "Neutral ⚪"

            # MACD
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            macd  = ema12 - ema26
            sig   = macd.ewm(span=9, adjust=False).mean()
            macd_val = macd.iloc[-1]
            sig_val  = sig.iloc[-1]
            macd_signal = ("Bullish Crossover 🟢 (MACD above Signal)"
                           if macd_val > sig_val
                           else "Bearish Crossover 🔴 (MACD below Signal)")

            # Trend
            if sma_50 and sma_200:
                if price > sma_50 > sma_200:
                    trend_signal = "Strong Uptrend 🚀 (above 50 & 200 SMA)"
                elif price < sma_50 < sma_200:
                    trend_signal = "Strong Downtrend 📉 (below 50 & 200 SMA)"
                elif price > sma_200:
                    trend_signal = "Long-term Bullish, Short-term Pullback ⚠️"
                else:
                    trend_signal = "Long-term Bearish, Short-term Bounce ⚠️"
            elif sma_50:
                trend_signal = "Above 50-SMA 📈" if price > sma_50 else "Below 50-SMA 📉"
            else:
                trend_signal = "Insufficient data"

            # 1-year return
            year_return = ((price - close.iloc[0]) / close.iloc[0] * 100) if close.iloc[0] else None

            tech_summary = f"""
### Technical Analysis (1-Year Data)
| Indicator | Value | Signal |
|---|---|---|
| **Current Price** | {fmt_price(price)} | — |
| **52-Week High** | {fmt_price(week52_high)} | {f'{((price/week52_high-1)*100):.1f}% from high' if isinstance(week52_high, (int,float)) else 'N/A'} |
| **52-Week Low**  | {fmt_price(week52_low)}  | {f'{((price/week52_low-1)*100):.1f}% from low' if isinstance(week52_low, (int,float)) else 'N/A'} |
| **50-Day SMA**   | {fmt_price(sma_50)}  | {'📈 Above' if sma_50 and price > sma_50 else '📉 Below'} |
| **200-Day SMA**  | {fmt_price(sma_200) if sma_200 else 'N/A (< 200 days data)'} | {'📈 Above' if sma_200 and price > sma_200 else '📉 Below' if sma_200 else '—'} |
| **RSI (14)**     | {rsi:.1f} | {rsi_signal} |
| **MACD**         | {macd_val:.4f} (Signal: {sig_val:.4f}) | {macd_signal} |
| **1-Year Return** | {f'{year_return:.1f}%' if year_return is not None else 'N/A'} | {'📈 Positive' if year_return and year_return > 0 else '📉 Negative'} |
| **Volume** | {f'{volume:,}' if isinstance(volume, (int,float)) else 'N/A'} | Avg: {f'{avg_volume:,}' if isinstance(avg_volume, (int,float)) else 'N/A'} |

**Overall Technical Bias**: {trend_signal}
"""
        else:
            tech_summary = "\n*Insufficient price history for technical indicators.*\n"

        # ── Overall Verdict ──
        signals = []
        if isinstance(rsi, float):
            if rsi < 35: signals.append("RSI oversold (+buy)")
            elif rsi > 70: signals.append("RSI overbought (-sell)")
        if macd_signal and "Bullish" in macd_signal: signals.append("MACD bullish (+)")
        elif macd_signal and "Bearish" in macd_signal: signals.append("MACD bearish (-)")
        if isinstance(pe_ratio, (int, float)):
            if pe_ratio < 15: signals.append("Low P/E (+value)")
            elif pe_ratio > 60: signals.append("High P/E (-expensive)")
        if isinstance(peg_ratio, (int, float)) and peg_ratio < 1.0:
            signals.append("PEG < 1 (+undervalued for growth)")

        bull_count = sum(1 for s in signals if "+" in s)
        bear_count = sum(1 for s in signals if "-" in s)
        if bull_count > bear_count:     verdict = "🟢 MODERATELY BULLISH"
        elif bear_count > bull_count:   verdict = "🔴 MODERATELY BEARISH"
        else:                            verdict = "⚪ NEUTRAL / MIXED"

        # ── Build Report ──
        report = f"""# Stock Analysis Report: {name} ({ticker_symbol})
*Generated by J.A.R.V.I.S on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')} IST*

## Company Overview
- **Exchange**: {'NSE India' if yf_symbol.endswith('.NS') else 'BSE India' if yf_symbol.endswith('.BO') else 'US Markets'}
- **Sector**: {sector} | **Industry**: {industry}
- **Current Price**: {fmt_price(price)}
- **Market Cap**: {fmt_cap(market_cap)}

{summary}

---

## Fundamental Valuation
| Metric | Value | Notes |
|---|---|---|
| **P/E Ratio (TTM)** | {pe_str} | {('<15 undervalued' if isinstance(pe_ratio,(int,float)) and pe_ratio < 15 else '>60 expensive' if isinstance(pe_ratio,(int,float)) and pe_ratio > 60 else 'Moderate')} |
| **Forward P/E** | {fpe_str} | Expected earnings |
| **PEG Ratio** | {peg_str} | <1.0 = undervalued for growth |
| **Price/Book** | {pb_str} | Book value multiple |
| **Debt/Equity** | {debt_to_equity} | Lower is safer |
| **Profit Margin** | {pm_str} | Net profitability |
| **ROE** | {roe_str} | Return on shareholders' equity |
| **Dividend Yield** | {dy_str} | Annual income return |
| **Free Cash Flow** | {fcf_str} | Cash after capex |

---
{tech_summary}
---

## JARVIS Verdict: {verdict}

**Signals**: {', '.join(signals) if signals else 'Neutral — no strong signal either way'}

> ⚠️ *This is for informational purposes only. Not financial advice.*
> *Always do your own research before trading.*
"""

        # Save report
        fname = f"stock_report_{ticker_symbol.replace('.', '_')}.md"
        Path(fname).write_text(report, encoding="utf-8")

        # Voice summary
        rsi_str   = f"RSI at {rsi:.0f} ({rsi_signal})" if rsi else ""
        trend_str = trend_signal or ""
        voice = (
            f"Stock analysis for {name} complete. "
            f"Current price: {fmt_price(price)}. "
            f"Market cap: {fmt_cap(market_cap)}. "
            f"P/E ratio: {pe_str}. Profit margin: {pm_str}. "
            f"{rsi_str}. {trend_str}. "
            f"Overall verdict: {verdict.replace('🟢','').replace('🔴','').replace('⚪','')}. "
            f"Full report saved as {fname}."
        )

        if player:
            player.write_log(f"[Stock] Analysis complete for {ticker_symbol}. Verdict: {verdict}")

        return voice

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return f"Error during stock analysis: {str(e)}"
