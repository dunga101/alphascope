import yfinance as yf


def collect_sector_breadth(symbols: list[str]) -> dict:
    sector_data = {}

    for symbol in symbols:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d")

        if hist.empty or len(hist) < 2:
            sector_data[symbol] = {
                "status": "NO_DATA"
            }
            continue

        latest_close = float(hist["Close"].iloc[-1])
        previous_close = float(hist["Close"].iloc[-2])
        change_pct = ((latest_close - previous_close) / previous_close) * 100

        sector_data[symbol] = {
            "latest_close": round(latest_close, 2),
            "change_pct": round(change_pct, 2),
            "status": "OK"
        }

    return sector_data
