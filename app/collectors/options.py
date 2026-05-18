import yfinance as yf


def collect_options_sentiment(symbols: list[str]) -> dict:
    options_data = {}

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)

            expirations = ticker.options

            if not expirations:
                options_data[symbol] = {
                    "status": "NO_OPTIONS"
                }
                continue

            nearest_expiry = expirations[0]

            chain = ticker.option_chain(nearest_expiry)

            total_calls = chain.calls["volume"].fillna(0).sum()
            total_puts = chain.puts["volume"].fillna(0).sum()

            put_call_ratio = (
                float(round(total_puts / total_calls, 2))
                if total_calls > 0
                else None
            )

            options_data[symbol] = {
                "status": "OK",
                "expiry": nearest_expiry,
                "call_volume": int(total_calls),
                "put_volume": int(total_puts),
                "put_call_ratio": put_call_ratio
            }

        except Exception as e:
            options_data[symbol] = {
                "status": f"ERROR: {str(e)}"
            }

    return options_data