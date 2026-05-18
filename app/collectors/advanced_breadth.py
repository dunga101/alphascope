import yfinance as yf


BREADTH_SYMBOLS = {
    "small_caps": "^RUT",
    "nasdaq_100": "^NDX",
    "sp500": "^GSPC",
    "dow": "^DJI",
}


def collect_advanced_breadth() -> dict:
    data = {}

    for label, symbol in BREADTH_SYMBOLS.items():
        try:
            hist = yf.Ticker(symbol).history(period="2d")

            if hist.empty or len(hist) < 2:
                data[label] = {
                    "status": "NO_DATA"
                }
                continue

            prev = float(hist["Close"].iloc[-2])
            current = float(hist["Close"].iloc[-1])

            change_pct = round(
                ((current - prev) / prev) * 100,
                2
            )

            data[label] = {
                "status": "OK",
                "symbol": symbol,
                "change_pct": change_pct
            }

        except Exception as e:
            data[label] = {
                "status": f"ERROR: {str(e)}"
            }

    return data