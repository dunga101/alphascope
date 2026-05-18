import yfinance as yf


def collect_market_sentiment() -> dict:
    try:
        vix = yf.Ticker("^VIX").history(period="2d")

        if vix.empty or len(vix) < 2:
            return {
                "status": "NO_DATA"
            }

        current = float(vix["Close"].iloc[-1])

        if current < 15:
            rating = "GREED"
        elif current < 20:
            rating = "NEUTRAL"
        elif current < 30:
            rating = "FEAR"
        else:
            rating = "EXTREME_FEAR"

        return {
            "status": "OK",
            "vix": round(current, 2),
            "rating": rating
        }

    except Exception as e:
        return {
            "status": f"ERROR: {str(e)}"
        }