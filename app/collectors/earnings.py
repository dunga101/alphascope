import yfinance as yf
from datetime import datetime, timezone


def classify_event_risk(days_until: int | None) -> str:
    if days_until is None:
        return "UNKNOWN"

    if days_until <= 2:
        return "HIGH"

    if days_until <= 7:
        return "MEDIUM"

    return "LOW"


def collect_earnings_context(symbols: list[str]) -> dict:
    earnings_data = {}
    now = datetime.now(timezone.utc)

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)

            earnings_dates = ticker.get_earnings_dates(limit=1)

            if earnings_dates is None or earnings_dates.empty:
                earnings_data[symbol] = {
                    "status": "NO_DATA",
                    "earnings_date": None,
                    "days_until": None,
                    "event_risk": "UNKNOWN"
                }
                continue

            earnings_date = earnings_dates.index[0]

            if hasattr(earnings_date, "to_pydatetime"):
                earnings_date = earnings_date.to_pydatetime()

            if earnings_date.tzinfo is None:
                earnings_date = earnings_date.replace(
                    tzinfo=timezone.utc
                )

            days_until = (earnings_date - now).days

            earnings_data[symbol] = {
                "status": "OK",
                "earnings_date": earnings_date.strftime("%Y-%m-%d"),
                "days_until": days_until,
                "event_risk": classify_event_risk(days_until)
            }

        except Exception as e:
            earnings_data[symbol] = {
                "status": f"ERROR: {str(e)}",
                "earnings_date": None,
                "days_until": None,
                "event_risk": "UNKNOWN"
            }

    return earnings_data