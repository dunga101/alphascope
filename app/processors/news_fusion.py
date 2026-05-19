from typing import List, Dict, Any
from urllib.parse import urlparse


HIGH_VALUE_SOURCES = {
    "Reuters": 8,
    "Bloomberg": 7,
    "CNBC": 3,
    "cnbc_markets": 4,
    "marketwatch_top": 2,
    "yahoo_finance": -4,
}


MARKET_KEYWORDS = {
    "fed": 8,
    "treasury": 8,
    "yield": 7,
    "inflation": 8,
    "interest rate": 8,
    "rates": 5,
    "economy": 5,
    "recession": 8,
    "earnings": 7,
    "guidance": 7,
    "forecast": 6,
    "profit warning": 7,
    "downgrade": 5,
    "upgrade": 4,
    "profit": 5,
    "margin": 5,
    "revenue": 5,
    "oil": 7,
    "gasoline": 5,
    "commodity": 5,
    "currency": 5,
    "bond": 6,
    "sanctions": 6,
    "shipping": 6,
    "trade": 5,
    "tariff": 6,
    "semiconductor": 5,
    "cloud": 4,
    "data center": 5,
    "ai infrastructure": 6,
    "gpu": 4,
    "capex": 4,
}


HARD_EXCLUDE_PATTERNS = [
    # Retail finance noise
    "jim cramer",
    "investing club",
    "top 10 things",
    "buy now",
    "hold for the long term",
    "high-yield stocks",
    "millionaire",
    "brilliant stocks",
    "motley fool",

    # Personal finance / consumer junk
    "inheritance",
    "child support",
    "doomjobbing",
    "mortgage calculator",

    # Political / legal gossip
    "lawsuit",
    "tax returns",
    "approval poll",
    "campaign trail",

    # Consumer gadget fluff
    "smart glasses",
    "audio glasses",
    "wearables",
    "first glimpse",
    "personal ai agent",

    # Sensational commentary
    "booking profits",
    "once-hated stock",
    "gone parabolic",
    "top stock picks",
    "must buy",

    # Clickbait / low signal
    "what's the mortgage rate",
    "earnings transcript",
    "put options",
    "short sellers",
]


POLITICAL_ALLOWED_TERMS = [
    "fed",
    "interest rate",
    "rates",
    "inflation",
    "treasury",
    "yield",
    "sanctions",
    "trade",
    "tariff",
    "economy",
]


POLITICAL_TRIGGER_TERMS = [
    "trump",
    "biden",
    "vance",
    "senate",
    "congress",
    "election",
    "campaign",
    "approval",
]


GEO_TRIGGER_TERMS = [
    "iran",
    "hormuz",
    "ukraine",
    "russia",
    "china",
    "taiwan",
    "gaza",
]


GEO_ALLOWED_TERMS = [
    "oil",
    "shipping",
    "inflation",
    "sanctions",
    "treasury",
    "yield",
    "currency",
    "commodity",
    "gasoline",
]


AI_ALLOWED_TERMS = [
    "data center",
    "cloud",
    "semiconductor",
    "gpu",
    "ai infrastructure",
    "openai",
    "anthropic",
    "capex",
]


EARNINGS_TERMS = [
    "earnings",
    "guidance",
    "forecast",
    "profit",
    "margin",
    "revenue",
    "downgrade",
    "upgrade",
]


def _text_blob(article: Dict[str, Any]) -> str:
    return (
        article.get("title", "") + " " +
        article.get("summary", "")
    ).lower()


def _canonical_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.netloc}{parsed.path}".lower()


def _deduplicate(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    output = []

    for article in articles:
        url = article.get("url", "")

        if not url:
            continue

        key = _canonical_url(url)

        if key in seen:
            continue

        seen.add(key)
        output.append(article)

    return output


def _hard_exclude(blob: str) -> bool:
    return any(term in blob for term in HARD_EXCLUDE_PATTERNS)


def _political_noise(blob: str) -> bool:
    triggered = any(term in blob for term in POLITICAL_TRIGGER_TERMS)

    if not triggered:
        return False

    allowed = any(term in blob for term in POLITICAL_ALLOWED_TERMS)

    return not allowed


def _geo_noise(blob: str) -> bool:
    triggered = any(term in blob for term in GEO_TRIGGER_TERMS)

    if not triggered:
        return False

    allowed = any(term in blob for term in GEO_ALLOWED_TERMS)

    return not allowed


def _bad_ai_story(blob: str) -> bool:
    if "ai" not in blob:
        return False

    allowed = any(term in blob for term in AI_ALLOWED_TERMS)

    return not allowed


def _is_market_relevant(blob: str) -> bool:
    if any(term in blob for term in EARNINGS_TERMS):
        return True

    return any(term in blob for term in MARKET_KEYWORDS)


def _score_article(article: Dict[str, Any]) -> int:
    blob = _text_blob(article)
    source = article.get("source", "")

    score = HIGH_VALUE_SOURCES.get(source, 0)

    for keyword, weight in MARKET_KEYWORDS.items():
        if keyword in blob:
            score += weight

    return score


def fuse_news(
    finnhub_articles: List[Dict[str, Any]],
    rss_articles: List[Dict[str, Any]],
    max_articles: int = 12
) -> List[Dict[str, Any]]:

    combined = finnhub_articles + rss_articles
    filtered = []

    for article in combined:
        blob = _text_blob(article)

        if _hard_exclude(blob):
            continue

        if _political_noise(blob):
            continue

        if _geo_noise(blob):
            continue

        if _bad_ai_story(blob):
            continue

        if not _is_market_relevant(blob):
            continue

        article["relevance_score"] = _score_article(article)
        filtered.append(article)

    deduped = _deduplicate(filtered)

    deduped.sort(
        key=lambda x: x["relevance_score"],
        reverse=True
    )

    return deduped[:max_articles]


if __name__ == "__main__":
    print("AlphaScope contextual news intelligence filter ready.")