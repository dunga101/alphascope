import yfinance as yf


def collect_insider_activity(symbols: list[str]) -> dict:
    data = {}

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)

            insider = ticker.insider_transactions

            if insider is None or insider.empty:
                data[symbol] = {
                    "status": "NO_DATA"
                }
                continue

            recent = insider.head(3)

            records = []

            for _, row in recent.iterrows():
                records.append({
                    "shares": row.get("Shares"),
                    "value": row.get("Value"),
                    "text": row.get("Text")
                })

            data[symbol] = {
                "status": "OK",
                "transactions": records
            }

        except Exception as e:
            data[symbol] = {
                "status": f"ERROR: {str(e)}"
            }

    return data