import yfinance as yf


def get_price_snapshot(ticker: str):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="6mo")

    if hist.empty:
        return None

    latest = hist.iloc[-1]
    previous = hist.iloc[-2]

    return {
        "ticker": ticker,
        "price": round(float(latest["Close"]), 2),
        "daily_change_pct": round(
            ((latest["Close"] - previous["Close"]) / previous["Close"]) * 100,
            2
        ),
        "volume": int(latest["Volume"]),
    }


if __name__ == "__main__":
    tickers = ["SPY", "QQQ", "NVDA", "MSFT", "SHOP.TO"]

    for ticker in tickers:
        result = get_price_snapshot(ticker)
        print(result)
