import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator


def calculate_indicators(ticker: str):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="6mo")

    if hist.empty or len(hist) < 50:
        return None

    hist["SMA20"] = hist["Close"].rolling(window=20).mean()
    hist["SMA50"] = hist["Close"].rolling(window=50).mean()

    rsi = RSIIndicator(close=hist["Close"], window=14)
    hist["RSI"] = rsi.rsi()

    latest = hist.iloc[-1]
    avg_volume_20 = hist["Volume"].tail(20).mean()

    volume_ratio = latest["Volume"] / avg_volume_20 if avg_volume_20 else 0

    return {
        "ticker": ticker,
        "price": round(float(latest["Close"]), 2),
        "sma20": round(float(latest["SMA20"]), 2),
        "sma50": round(float(latest["SMA50"]), 2),
        "rsi": round(float(latest["RSI"]), 2),
        "volume_ratio": round(float(volume_ratio), 2),
    }


if __name__ == "__main__":
    tickers = ["SPY", "QQQ", "NVDA", "MSFT", "SHOP.TO"]

    for ticker in tickers:
        print(calculate_indicators(ticker))
