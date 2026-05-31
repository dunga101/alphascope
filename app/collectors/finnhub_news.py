import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

from app.logger import setup_logger

load_dotenv(".env")

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
log = setup_logger()


def collect_finnhub_news(days_back: int = 1, limit: int = 30):
    if not FINNHUB_API_KEY:
        log.warning("Finnhub news collection skipped: FINNHUB_API_KEY missing")
        return []

    today = datetime.utcnow().date()
    start = today - timedelta(days=days_back)

    url = "https://finnhub.io/api/v1/news"

    params = {
        "category": "general",
        "minId": 0,
        "token": FINNHUB_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()

        data = response.json()

    except requests.exceptions.RequestException as e:
        log.warning(f"Finnhub news collection failed: {e}")
        return []

    except ValueError as e:
        log.warning(f"Finnhub news payload could not be decoded: {e}")
        return []

    if not isinstance(data, list):
        log.warning("Finnhub news collection returned unexpected payload shape")
        return []

    articles = []

    for item in data[:limit]:
        articles.append({
            "source_type": "finnhub",
            "source": item.get("source", "finnhub"),
            "title": item.get("headline", ""),
            "summary": item.get("summary", ""),
            "url": item.get("url", ""),
            "published": item.get("datetime", 0),
        })

    return articles


if __name__ == "__main__":
    from pprint import pprint
    pprint(collect_finnhub_news())
