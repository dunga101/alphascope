import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv


load_dotenv(".env")

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")


def collect_finnhub_news(days_back: int = 1, limit: int = 30):
    if not FINNHUB_API_KEY:
        raise ValueError("FINNHUB_API_KEY missing")

    today = datetime.utcnow().date()
    start = today - timedelta(days=days_back)

    url = "https://finnhub.io/api/v1/news"

    params = {
        "category": "general",
        "minId": 0,
        "token": FINNHUB_API_KEY
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()

    data = response.json()

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