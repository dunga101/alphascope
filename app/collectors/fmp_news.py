import os
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv


load_dotenv(".env")

FMP_API_KEY = os.getenv("FMP_API_KEY")

BASE_URL = "https://financialmodelingprep.com/stable"

CACHE_DIR = Path("data/cache/fmp_news")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

MARKET_NEWS_CACHE_SECONDS = 3600
SYMBOL_NEWS_CACHE_SECONDS = 7200


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cache_path(name: str) -> Path:
    safe = name.replace("/", "_").replace(":", "_").replace(" ", "_")
    return CACHE_DIR / f"{safe}.json"


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


def _get_json(endpoint: str, params: Dict[str, Any]) -> Any:
    if not FMP_API_KEY:
        raise ValueError("FMP_API_KEY not found in .env")

    request_params = dict(params)
    request_params["apikey"] = FMP_API_KEY

    url = f"{BASE_URL}/{endpoint.lstrip('/')}"

    response = requests.get(url, params=request_params, timeout=20)
    response.raise_for_status()

    return response.json()


def _normalize_article(
    article: Dict[str, Any],
    default_symbol: Optional[str] = None
) -> Dict[str, Any]:
    symbol = (
        article.get("symbol")
        or article.get("ticker")
        or default_symbol
        or "MARKET"
    )

    title = (
        article.get("title")
        or article.get("headline")
        or ""
    )

    published = (
        article.get("publishedDate")
        or article.get("date")
        or ""
    )

    source = (
        article.get("site")
        or article.get("source")
        or article.get("publisher")
        or ""
    )

    url = article.get("url") or article.get("link") or ""

    summary = (
        article.get("text")
        or article.get("summary")
        or article.get("content")
        or ""
    )

    return {
        "symbol": str(symbol).upper(),
        "title": str(title).strip(),
        "source": str(source).strip(),
        "published": str(published).strip(),
        "url": str(url).strip(),
        "summary": str(summary).strip(),
    }


def _normalize_news(
    raw_news: Any,
    default_symbol: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    if not isinstance(raw_news, list):
        return []

    normalized = []

    for article in raw_news[:limit]:
        if not isinstance(article, dict):
            continue

        item = _normalize_article(article, default_symbol)

        if item["title"]:
            normalized.append(item)

    return normalized


def collect_market_news(
    limit: int = 10,
    use_cache: bool = True
) -> List[Dict[str, Any]]:
    cache_file = _cache_path("market_news")

    if use_cache:
        cached = _read_cache(cache_file, MARKET_NEWS_CACHE_SECONDS)
        if cached and "data" in cached:
            return cached["data"]

    raw = _get_json(
        endpoint="fmp-articles",
        params={
            "page": 0,
            "limit": limit,
        },
    )

    normalized = _normalize_news(
        raw,
        default_symbol="MARKET",
        limit=limit,
    )

    _write_cache(cache_file, normalized)

    return normalized


def collect_symbol_news(
    symbol: str,
    limit: int = 5,
    use_cache: bool = True
) -> List[Dict[str, Any]]:
    symbol = symbol.upper().strip()

    cache_file = _cache_path(f"symbol_news_{symbol}")

    if use_cache:
        cached = _read_cache(cache_file, SYMBOL_NEWS_CACHE_SECONDS)
        if cached and "data" in cached:
            return cached["data"]

    raw = _get_json(
        endpoint="news/stock",
        params={
            "symbols": symbol,
            "limit": limit,
        },
    )

    normalized = _normalize_news(
        raw,
        default_symbol=symbol,
        limit=limit,
    )

    _write_cache(cache_file, normalized)

    return normalized


def collect_news_context(
    symbols: Optional[List[str]] = None,
    market_limit: int = 8,
    symbol_limit: int = 3,
    use_cache: bool = True
) -> Dict[str, Any]:
    symbols = symbols or []

    context = {
        "market_news": [],
        "symbol_news": {},
    }

    try:
        context["market_news"] = collect_market_news(
            limit=market_limit,
            use_cache=use_cache,
        )
    except Exception as exc:
        context["market_news"] = [
            {
                "symbol": "MARKET",
                "title": "Market news collection failed",
                "source": "AlphaScope",
                "published": _now_utc(),
                "url": "",
                "summary": str(exc),
            }
        ]

    for symbol in symbols:
        clean_symbol = symbol.upper().strip()

        if not clean_symbol:
            continue

        try:
            context["symbol_news"][clean_symbol] = collect_symbol_news(
                clean_symbol,
                limit=symbol_limit,
                use_cache=use_cache,
            )
        except Exception as exc:
            context["symbol_news"][clean_symbol] = [
                {
                    "symbol": clean_symbol,
                    "title": "Symbol news collection failed",
                    "source": "AlphaScope",
                    "published": _now_utc(),
                    "url": "",
                    "summary": str(exc),
                }
            ]

    return context


if __name__ == "__main__":
    test_symbols = ["SPY", "QQQ", "NVDA", "MSFT"]

    news = collect_news_context(
        symbols=test_symbols,
        market_limit=5,
        symbol_limit=2,
        use_cache=False,
    )

    print(json.dumps(news, indent=2))