import yfinance as yf


def collect_analyst_sentiment(symbols: list[str]) -> dict:
    data = {}

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)

            info = ticker.info

            data[symbol] = {
                "status": "OK",
                "recommendation": info.get("recommendationKey"),
                "target_mean_price": info.get("targetMeanPrice"),
                "current_price": info.get("currentPrice")
            }

        except Exception as e:
            data[symbol] = {
                "status": f"ERROR: {str(e)}"
            }

    return data