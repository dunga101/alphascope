import time
import feedparser
from datetime import datetime, timezone
from typing import List, Dict, Any


RSS_FEEDS = {
    "cnbc_markets": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "marketwatch_top": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    "reuters_business": "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best",
    "yahoo_finance": "https://finance.yahoo.com/news/rssindex",
}


def _parse_entry(feed_name: str, entry: Any) -> Dict[str, Any]:
    published = entry.get("published", "") or entry.get("updated", "")

    return {
        "source_type": "rss",
        "source": feed_name,
        "title": entry.get("title", "").strip(),
        "summary": entry.get("summary", "").strip(),
        "url": entry.get("link", "").strip(),
        "published": published,
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }


def collect_rss_news(limit_per_feed: int = 10) -> List[Dict[str, Any]]:
    articles = []

    for feed_name, feed_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries[:limit_per_feed]:
                article = _parse_entry(feed_name, entry)

                if article["title"]:
                    articles.append(article)

            time.sleep(0.5)

        except Exception as e:
            articles.append({
                "source_type": "rss",
                "source": feed_name,
                "error": str(e),
                "collected_at": datetime.now(timezone.utc).isoformat(),
            })

    return articles


if __name__ == "__main__":
    from pprint import pprint
    pprint(collect_rss_news())
