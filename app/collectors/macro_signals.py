import yfinance as yf


MACRO_SYMBOLS = {
    "vix": "^VIX",
    "ten_year_yield": "^TNX",
    "technology": "XLK",
    "financials": "XLF",
    "energy": "XLE",
    "utilities": "XLU",
    "staples": "XLP",
    "discretionary": "XLY",
}


def get_change_pct(symbol: str):
    try:
        data = yf.Ticker(symbol).history(period="5d")

        if data.empty or len(data) < 2:
            return None

        previous_close = float(data["Close"].iloc[-2])
        latest_close = float(data["Close"].iloc[-1])

        change_pct = ((latest_close - previous_close) / previous_close) * 100

        return round(change_pct, 2)

    except Exception:
        return None


def collect_macro_signals():
    results = {}

    for name, symbol in MACRO_SYMBOLS.items():
        change_pct = get_change_pct(symbol)

        results[name] = {
            "symbol": symbol,
            "change_pct": change_pct,
            "status": "OK" if change_pct is not None else "ERROR",
        }

    return results