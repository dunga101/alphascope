import os
import json
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

import finnhub
from dotenv import load_dotenv


load_dotenv(".env")

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

CACHE_DIR = Path("data/cache/finnhub_news")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

SYMBOL_NEWS_CACHE_SECONDS = 60 * 60 * 2  # 2 hours


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _days_ago(days: int) -> str:
    return (datetime.now(timezone.utc).date() - timedelta(days=days)).isoformat()


def _cache_path(name: str) -> Path:
    safe_name = name.replace("/", "_").replace(":", "_").replace(" ", "_")
    return CACHE_DIR / f"{safe_name}.json"


def _read_cache(path: Path, max_age_seconds: int) -> Optional[Any]:
    if not path.exists():
        return None

    age = time.time() - path.stat().st_mtime

    if age > max_age_seconds:
        return None

    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _write_cache(path: Path, data: Any) -> None:
    payload = {
        "cached_at": _now_utc(),
        "data": data,
    }

    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _client() -> finnhub.Client:
    if not FINNHUB_API_KEY:
        raise ValueError("FINNHUB_API_KEY not found in .env")

    return finnhub.Client(api_key=FINNHUB_API_KEY)


def _normalize_article(
    article: Dict[str, Any],
    default_symbol: str
) -> Dict[str, Any]:
    timestamp = article.get("datetime")

    if isinstance(timestamp, int):
        published = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
    else:
        published = str(timestamp or "")

    return {
        "symbol": default_symbol.upper(),
        "title": str(article.get("headline") or "").strip(),
        "source": str(article.get("source") or "Finnhub").strip(),
        "published": published,
        "url": str(article.get("url") or "").strip(),
        "summary": str(article.get("summary") or "").strip(),
        "image": str(article.get("image") or "").strip(),
        "provider": "Finnhub",
    }


def _normalize_news(
    raw_news: Any,
    symbol: str,
    limit: int
) -> List[Dict[str, Any]]:
    if not isinstance(raw_news, list):
        return []

    normalized = []

    for article in raw_news[:limit]:
        if not isinstance(article, dict):
            continue

        item = _normalize_article(article, default_symbol=symbol)

        if item["title"]:
            normalized.append(item)

    return normalized


def collect_symbol_news(
    symbol: str,
    days_back: int = 7,
    limit: int = 5,
    use_cache: bool = True
) -> List[Dict[str, Any]]:
    symbol = symbol.upper().strip()

    if not symbol:
        return []

    cache_file = _cache_path(f"{symbol}_{days_back}d_{limit}")

    if use_cache:
        cached = _read_cache(cache_file, SYMBOL_NEWS_CACHE_SECONDS)
        if cached and "data" in cached:
            return cached["data"]

    client = _client()

    raw = client.company_news(
        symbol,
        _days_ago(days_back),
        _today(),
    )

    normalized = _normalize_news(
        raw_news=raw,
        symbol=symbol,
        limit=limit,
    )

    _write_cache(cache_file, normalized)

    return normalized


def collect_finnhub_news_context(
    symbols: List[str],
    days_back: int = 7,
    limit_per_symbol: int = 5,
    use_cache: bool = True
) -> Dict[str, Any]:
    context = {
        "provider": "Finnhub",
        "generated_at": _now_utc(),
        "symbol_news": {},
    }

    for symbol in symbols:
        clean_symbol = symbol.upper().strip()

        if not clean_symbol:
            continue

        try:
            context["symbol_news"][clean_symbol] = collect_symbol_news(
                symbol=clean_symbol,
                days_back=days_back,
                limit=limit_per_symbol,
                use_cache=use_cache,
            )
        except Exception as exc:
            context["symbol_news"][clean_symbol] = [
                {
                    "symbol": clean_symbol,
                    "title": "Finnhub news collection failed",
                    "source": "AlphaScope",
                    "published": _now_utc(),
                    "url": "",
                    "summary": str(exc),
                    "image": "",
                    "provider": "Finnhub",
                }
            ]

    return context


if __name__ == "__main__":
    test_symbols = ["AAPL", "MSFT", "NVDA", "TSLA"]

    result = collect_finnhub_news_context(
        symbols=test_symbols,
        days_back=7,
        limit_per_symbol=3,
        use_cache=False,
    )

    print(json.dumps(result, indent=2))
