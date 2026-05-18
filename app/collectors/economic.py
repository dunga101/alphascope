import feedparser


ECONOMIC_FEEDS = {
    "investing_macro": "https://www.investing.com/rss/news_285.rss",
    "marketwatch_economy": "https://feeds.marketwatch.com/marketwatch/economy"
}


def collect_economic_calendar(limit_per_feed: int = 5) -> dict:
    data = {}

    for source, url in ECONOMIC_FEEDS.items():
        try:
            feed = feedparser.parse(url)

            items = []

            for entry in feed.entries[:limit_per_feed]:
                items.append({
                    "title": entry.get("title", "UNKNOWN"),
                    "published": entry.get("published", "UNKNOWN"),
                    "link": entry.get("link", "")
                })

            data[source] = {
                "status": "OK",
                "items": items
            }

        except Exception as e:
            data[source] = {
                "status": f"ERROR: {str(e)}",
                "items": []
            }

    return data