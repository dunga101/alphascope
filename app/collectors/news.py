import feedparser


RSS_FEEDS = {
    "marketwatch": "https://feeds.marketwatch.com/marketwatch/topstories/",
    "yahoo_finance": "https://finance.yahoo.com/news/rssindex",
}


def collect_news_context(limit_per_feed: int = 5) -> dict:
    news = {}

    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            items = []

            for entry in feed.entries[:limit_per_feed]:
                items.append({
                    "title": entry.get("title", "UNKNOWN"),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", "UNKNOWN"),
                })

            news[source] = {
                "status": "OK",
                "items": items
            }

        except Exception as e:
            news[source] = {
                "status": f"ERROR: {str(e)}",
                "items": []
            }

    return news