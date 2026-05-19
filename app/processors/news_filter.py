from typing import Dict, List

from app.config.ticker_aliases import TICKER_ALIASES


LOW_SIGNAL_KEYWORDS = [
    "most active stocks",
    "top stocks to watch",
    "best dividend",
    "income investors",
    "weekly roundup",
    "market recap",
    "watch these stocks",
    "hot stocks",
    "top gainers",
    "top losers",
    "stocks to buy now",
    "trending stocks",
]


HARD_SUPPRESS_KEYWORDS = [
    "crypto",
    "blockchain",
    "tokenized",
    "tokenizing",
    "digital asset",
    "web3",
    "nft",
    "defi",
    "dogecoin",
    "bitcoin etf",
    "altcoin",
    "passive income",
    "retirement portfolio",
    "buy, sell or hold",
    "buy sell or hold",
    "millionaires",
    "best stock",
    "top picks",
    "dividend aristocrat",
    "monthly income",
]


HIGH_SIGNAL_KEYWORDS = [
    "earnings",
    "guidance",
    "revenue",
    "margin",
    "forecast",
    "sec",
    "lawsuit",
    "investigation",
    "acquisition",
    "merger",
    "downgrade",
    "upgrade",
    "price target",
    "fed",
    "treasury",
    "yield",
    "inflation",
    "tariff",
    "recall",
    "delivery",
    "shipments",
    "product launch",
    "ai",
    "chip",
    "regulation",
    "approval",
    "ban",
    "antitrust",
    "data center",
]


HIGH_TRUST_SOURCES = [
    "Reuters",
    "Bloomberg",
    "Wall Street Journal",
    "CNBC",
    "Yahoo",
    "Financial Times",
    "MarketWatch",
]


def _article_text(article: Dict) -> str:
    title = article.get("title", "")
    summary = article.get("summary", "")
    return f"{title} {summary}".lower().strip()


def _source_name(article: Dict) -> str:
    return str(article.get("source", "")).strip()


def _contains_any(text: str, keywords: List[str]) -> bool:
    return any(keyword.lower() in text for keyword in keywords)


def _is_relevant_to_symbol(symbol: str, article: Dict) -> bool:
    text = _article_text(article)

    aliases = TICKER_ALIASES.get(
        symbol.upper(),
        [symbol.lower()]
    )

    return any(alias.lower() in text for alias in aliases)


def _hard_reject(article: Dict) -> bool:
    text = _article_text(article)

    if _contains_any(text, HARD_SUPPRESS_KEYWORDS):
        return True

    return False


def score_article(article: Dict) -> Dict:
    text = _article_text(article)
    source = _source_name(article)

    score = 0
    reasons = []

    if _contains_any(text, LOW_SIGNAL_KEYWORDS):
        score -= 50
        reasons.append("low_signal_keyword")

    if _contains_any(text, HIGH_SIGNAL_KEYWORDS):
        score += 40
        reasons.append("high_signal_keyword")

    if source in HIGH_TRUST_SOURCES:
        score += 20
        reasons.append("trusted_source")

    if len(article.get("summary", "")) > 100:
        score += 10
        reasons.append("has_summary")

    if article.get("url"):
        score += 5
        reasons.append("has_url")

    return {
        "score": score,
        "reasons": reasons,
    }


def filter_articles(
    symbol: str,
    articles: List[Dict],
    min_score: int = 20,
    max_results: int = 5,
) -> List[Dict]:
    scored_articles = []

    for article in articles:
        if not _is_relevant_to_symbol(symbol, article):
            continue

        if _hard_reject(article):
            continue

        scoring = score_article(article)

        if scoring["score"] < min_score:
            continue

        enriched = dict(article)
        enriched["quality_score"] = scoring["score"]
        enriched["quality_reasons"] = scoring["reasons"]

        scored_articles.append(enriched)

    scored_articles.sort(
        key=lambda x: x["quality_score"],
        reverse=True
    )

    return scored_articles[:max_results]


def filter_news_context(
    news_context: Dict,
    min_score: int = 20,
    max_results_per_symbol: int = 3,
) -> Dict:
    filtered = {
        "provider": news_context.get("provider", "Unknown"),
        "generated_at": news_context.get("generated_at"),
        "symbol_news": {},
    }

    for symbol, articles in news_context.get("symbol_news", {}).items():
        filtered["symbol_news"][symbol] = filter_articles(
            symbol=symbol,
            articles=articles,
            min_score=min_score,
            max_results=max_results_per_symbol,
        )

    return filtered


if __name__ == "__main__":
    import json
    from app.collectors.finnhub_news import collect_finnhub_news_context

    raw = collect_finnhub_news_context(
        symbols=["AAPL", "MSFT", "NVDA", "TSLA"],
        days_back=7,
        limit_per_symbol=10,
        use_cache=True,
    )

    filtered = filter_news_context(
        raw,
        min_score=20,
        max_results_per_symbol=3,
    )

    print(json.dumps(filtered, indent=2))