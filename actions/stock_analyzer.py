import os
from pathlib import Path
import yfinance as yf
import pandas as pd
import numpy as np

def stock_analyzer(parameters=None, player=None, **kwargs):
    # Support both direct calling and dict parameter structure
    ticker_symbol = ""
    if isinstance(parameters, dict):
        ticker_symbol = parameters.get("ticker", "").strip().upper()
    elif isinstance(parameters, str):
        ticker_symbol = parameters.strip().upper()
    
    if not ticker_symbol:
        return "Error: No ticker symbol provided."

    print(f"[Stock Analyzer] Analyzing stock symbol: {ticker_symbol}")
    
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        if not info or 'regularMarketPrice' not in info and 'currentPrice' not in info:
            # Try fetching history first in case info is empty (common for some global tickers)
            history = ticker.history(period="1y")
            if history.empty:
                return f"Error: Could not retrieve data for ticker symbol '{ticker_symbol}'. Please verify the symbol is correct."
        else:
            history = ticker.history(period="1y")
            
        # Get fundamental metrics
        name = info.get("longName", ticker_symbol)
        sector = info.get("sector", "N/A")
        industry = info.get("industry", "N/A")
        summary = info.get("longBusinessSummary", "No summary available.")
        
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        if not price and not history.empty:
            price = history['Close'].iloc[-1]
            
        market_cap = info.get("marketCap", 0)
        pe_ratio = info.get("trailingPE", "N/A")
        forward_pe = info.get("forwardPE", "N/A")
        peg_ratio = info.get("pegRatio", "N/A")
        pb_ratio = info.get("priceToBook", "N/A")
        debt_to_equity = info.get("debtToEquity", "N/A")
        profit_margin = info.get("profitMargins", "N/A")
        roe = info.get("returnOnEquity", "N/A")
        div_yield = info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0
        free_cash_flow = info.get("freeCashflow", "N/A")

        # Format metrics for display
        market_cap_str = f"${market_cap/1e9:.2f}B" if market_cap else "N/A"
        pe_str = f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else "N/A"
        forward_pe_str = f"{forward_pe:.2f}" if isinstance(forward_pe, (int, float)) else "N/A"
        peg_str = f"{peg_ratio:.2f}" if isinstance(peg_ratio, (int, float)) else "N/A"
        pb_str = f"{pb_ratio:.2f}" if isinstance(pb_ratio, (int, float)) else "N/A"
        profit_margin_str = f"{profit_margin*100:.2f}%" if isinstance(profit_margin, (int, float)) else "N/A"
        roe_str = f"{roe*100:.2f}%" if isinstance(roe, (int, float)) else "N/A"
        div_yield_str = f"{div_yield:.2f}%" if div_yield else "0.00%"
        fcf_str = f"${free_cash_flow/1e6:.2f}M" if isinstance(free_cash_flow, (int, float)) else "N/A"

        # Technical Indicators Calculations
        technical_summary = ""
        if not history.empty and len(history) >= 50:
            close_prices = history['Close']
            
            # Simple Moving Averages (SMA)
            sma_50 = close_prices.rolling(window=50).mean().iloc[-1]
            sma_200 = close_prices.rolling(window=200).mean().iloc[-1] if len(close_prices) >= 200 else None
            
            # RSI Calculation
            delta = close_prices.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            
            rs = avg_gain / (avg_loss + 1e-10)
            rsi_series = 100 - (100 / (1 + rs))
            rsi = rsi_series.iloc[-1]
            
            # MACD Calculation
            ema_12 = close_prices.ewm(span=12, adjust=False).mean()
            ema_26 = close_prices.ewm(span=26, adjust=False).mean()
            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            
            latest_macd = macd_line.iloc[-1]
            latest_signal = signal_line.iloc[-1]

            # Signal Determinations
            rsi_signal = "Neutral"
            if rsi > 70:
                rsi_signal = "Overbought (Potential Sell Alert)"
            elif rsi < 30:
                rsi_signal = "Oversold (Potential Buy Alert)"
                
            trend_signal = "Neutral"
            if sma_200:
                if price > sma_50 > sma_200:
                    trend_signal = "Strong Bullish Trend (Price above 50 SMA & 200 SMA)"
                elif price < sma_50 < sma_200:
                    trend_signal = "Strong Bearish Trend (Price below 50 SMA & 200 SMA)"
                elif price > sma_200 and price < sma_50:
                    trend_signal = "Weak Bearish (Short-term pull back, long-term bullish)"
                elif price < sma_200 and price > sma_50:
                    trend_signal = "Weak Bullish (Short-term recovery, long-term bearish)"
            else:
                if price > sma_50:
                    trend_signal = "Bullish Trend (Price above 50 SMA)"
                else:
                    trend_signal = "Bearish Trend (Price below 50 SMA)"
            
            macd_signal = "Neutral"
            if latest_macd > latest_signal:
                macd_signal = "Bullish Crossover (MACD line above Signal line)"
            else:
                macd_signal = "Bearish Crossover (MACD line below Signal line)"

            technical_summary = f"""
### Technical Analysis Indicators (1 Year Data)
| Indicator | Value | Signal / Assessment |
|---|---|---|
| **Current Price** | ${price:.2f} | Current trading level |
| **50-Day SMA** | ${sma_50:.2f} | {"Above SMA 50" if price > sma_50 else "Below SMA 50"} |
| **200-Day SMA** | {f"${sma_200:.2f}" if sma_200 else "N/A"} | {"Above SMA 200" if sma_200 and price > sma_200 else "Below SMA 200" if sma_200 else "N/A"} |
| **RSI (14)** | {rsi:.2f} | {rsi_signal} |
| **MACD Line** | {latest_macd:.4f} | {macd_signal} (Signal Line: {latest_signal:.4f}) |

**Overall Technical Bias**: {trend_signal}
"""
        else:
            technical_summary = "\n*Note: Insufficient historical price data to calculate technical indicators (Requires at least 50 days of history).* "

        # Generate markdown report content
        report_content = f"""# Financial & Technical Analysis Report: {name} ({ticker_symbol})
Generated autonomously by J.A.R.V.I.S on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

## Company Overview
- **Sector**: {sector}
- **Industry**: {industry}
- **Current Stock Price**: ${price:.2f}

### Business Description
{summary}

---

## Fundamental Valuation metrics
| Metric | Value | Description |
|---|---|---|
| **Market Capitalization** | {market_cap_str} | Total value of company's outstanding shares |
| **Trailing P/E Ratio** | {pe_str} | Valuation ratio (Price / Earnings) |
| **Forward P/E Ratio** | {forward_pe_str} | Projected P/E ratio based on earnings forecasts |
| **PEG Ratio** | {peg_str} | Price/Earnings-to-Growth ratio (value of < 1.0 is often considered cheap) |
| **Price-to-Book (P/B) Ratio** | {pb_str} | Price relative to book value |
| **Debt to Equity Ratio** | {debt_to_equity} | Total liabilities divided by shareholder equity |
| **Profit Margin** | {profit_margin_str} | Ratio of net profit to total revenue |
| **Return on Equity (ROE)** | {roe_str} | Performance metric (net income / shareholder equity) |
| **Dividend Yield** | {div_yield_str} | Annual dividend payment relative to stock price |
| **Free Cash Flow (FCF)** | {fcf_str} | Operating cash flow minus capital expenditures |

---

{technical_summary}

---

## Autonomous Summary Assessment
- **Valuation Assessment**: {"Fairly Valued / Growth priced in" if peg_ratio == 'N/A' or (isinstance(peg_ratio, (int,float)) and peg_ratio > 1.5) else "Undervalued Relative to Growth" if isinstance(peg_ratio, (int,float)) and peg_ratio < 1.0 else "Neutral Valuation"}
- **Technical Position**: {trend_signal.split(" (")[0] if "trend_signal" in locals() else "N/A"}
- **Key Strengths**: High profit margins ({profit_margin_str}) and solid ROE ({roe_str}).
- **Recommended Action**: Please consult the full chart history and financial filings before trading. This report is compiled for informational purposes only.
"""

        # Save report to a local markdown file
        filename = f"stock_report_{ticker_symbol}.md"
        report_path = Path(filename).resolve()
        report_path.write_text(report_content, encoding="utf-8")
        
        # Build voice/chat summary output
        voice_summary = (
            f"SYS: Stock analysis for {name} ({ticker_symbol}) completed. "
            f"Current price is ${price:.2f}. "
            f"Fundamentals: P/E is {pe_str}, Profit Margin is {profit_margin_str}. "
            f"Technicals: RSI is {rsi:.2f} ({rsi_signal}). MACD is {macd_signal}. "
            f"The detailed report has been saved to '{filename}'."
        )
        
        if player:
            player.write_log(f"SYS: Stock report compiled for {ticker_symbol}.")
            
        return voice_summary

    except Exception as e:
        return f"Error occurred during stock analysis: {str(e)}"
