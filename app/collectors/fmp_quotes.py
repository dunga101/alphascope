import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

load_dotenv(".env")

FMP_API_KEY = os.getenv("FMP_API_KEY")
CACHE_MINUTES = int(os.getenv("FMP_CACHE_MINUTES", "30"))

CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

FMP_BASE_URL = "https://financialmodelingprep.com/stable/quote"


def _build_session() -> requests.Session:
    session = requests.Session()

    retries = Retry(
        total=2,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(max_retries=retries)

    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


SESSION = _build_session()


def _cache_file(symbol: str) -> Path:
    safe_symbol = symbol.replace("/", "_")
    return CACHE_DIR / f"fmp_{safe_symbol}.json"


def _cache_age_seconds(symbol: str) -> float:
    cache = _cache_file(symbol)

    if not cache.exists():
        return -1

    return time.time() - cache.stat().st_mtime


def _cache_is_valid(symbol: str) -> bool:
    age = _cache_age_seconds(symbol)

    if age < 0:
        return False

    return age < CACHE_MINUTES * 60


def _load_cache(symbol: str) -> Dict[str, Any]:
    with open(_cache_file(symbol), "r", encoding="utf-8") as f:
        return json.load(f)


def _save_cache(symbol: str, data: Dict[str, Any]) -> None:
    with open(_cache_file(symbol), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _validate_quote(item: Dict[str, Any], requested_symbol: str) -> None:
    if not item:
        raise ValueError(f"Empty API payload for {requested_symbol}")

    returned_symbol = item.get("symbol")

    if not returned_symbol:
        raise ValueError(f"Missing symbol in API response for {requested_symbol}")

    if returned_symbol.upper() != requested_symbol.upper():
        raise ValueError(
            f"Symbol mismatch. Requested={requested_symbol}, Returned={returned_symbol}"
        )

    if item.get("price") is None:
        raise ValueError(f"Missing price for {requested_symbol}")


def _normalize_quote(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "symbol": item.get("symbol"),
        "name": item.get("name"),
        "price": item.get("price"),
        "change": item.get("change"),
        "changePercentage": item.get("changePercentage"),
        "volume": item.get("volume"),
        "dayLow": item.get("dayLow"),
        "dayHigh": item.get("dayHigh"),
        "yearLow": item.get("yearLow"),
        "yearHigh": item.get("yearHigh"),
        "marketCap": item.get("marketCap"),
        "priceAvg50": item.get("priceAvg50"),
        "priceAvg200": item.get("priceAvg200"),
        "open": item.get("open"),
        "previousClose": item.get("previousClose"),
        "timestamp": item.get("timestamp"),
        "exchange": item.get("exchange"),
    }


def _fetch_single_symbol(symbol: str) -> Dict[str, Any]:
    symbol = symbol.strip().upper()

    if _cache_is_valid(symbol):
        cached = _load_cache(symbol)
        cached["cache_status"] = "HIT"
        cached["cache_age_seconds"] = round(_cache_age_seconds(symbol), 1)
        return cached

    params = {
        "symbol": symbol,
        "apikey": FMP_API_KEY,
    }

    response = SESSION.get(FMP_BASE_URL, params=params, timeout=15)
    response.raise_for_status()

    raw_data = response.json()

    if not isinstance(raw_data, list):
        raise ValueError(f"Unexpected API response format for {symbol}")

    if not raw_data:
        raise ValueError(f"No quote data returned for {symbol}")

    item = raw_data[0]

    _validate_quote(item, symbol)

    result = {
        "status": "OK",
        "source": "FMP",
        "cache_status": "MISS",
        "cache_age_seconds": 0,
        "quote": _normalize_quote(item),
    }

    _save_cache(symbol, result)

    return result


def collect_fmp_quotes(symbols: List[str]) -> Dict[str, Any]:
    if not FMP_API_KEY:
        return {
            "status": "ERROR",
            "source": "FMP",
            "error": "Missing FMP_API_KEY in .env",
            "quotes": {},
            "errors": {},
            "cache_stats": {},
        }

    quotes = {}
    errors = {}
    cache_stats = {
        "hits": 0,
        "misses": 0,
    }

    for symbol in symbols:
        try:
            result = _fetch_single_symbol(symbol)

            if result["cache_status"] == "HIT":
                cache_stats["hits"] += 1
            else:
                cache_stats["misses"] += 1

            quotes[symbol.upper()] = result["quote"]

        except Exception as e:
            errors[symbol.upper()] = str(e)

    return {
        "status": "OK" if quotes else "ERROR",
        "source": "FMP",
        "quotes": quotes,
        "errors": errors,
        "cache_stats": cache_stats,
    }