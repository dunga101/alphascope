from app.collectors.finnhub_news import collect_finnhub_news
from app.collectors.rss_news import collect_rss_news
from app.processors.news_fusion import fuse_news


def collect_news_intelligence():
    finnhub = collect_finnhub_news(limit=30)
    rss = collect_rss_news(limit_per_feed=10)

    fused = fuse_news(
        finnhub_articles=finnhub,
        rss_articles=rss,
        max_articles=20
    )

    return fused


if __name__ == "__main__":
    from pprint import pprint
    pprint(collect_news_intelligence())
