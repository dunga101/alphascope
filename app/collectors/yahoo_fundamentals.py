import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = Path("data/cache/yahoo_fundamentals")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_VERSION = 2

YAHOO_FUNDAMENTAL_CACHE_HOURS = int(
    os.getenv("YAHOO_FUNDAMENTAL_CACHE_HOURS", "24")
)

YAHOO_FIELD_MAP = {
    "pe_ratio": "trailingPE",
    "forward_pe": "forwardPE",
    "dividend_yield": "dividendYield",
    "roe": "returnOnEquity",
    "market_cap": "marketCap",
    "sector": "sector",
    "industry": "industry",
    "revenue": "totalRevenue",
    "operating_margin": "operatingMargins",
    "net_margin": "profitMargins",
    "profit_margin": "profitMargins",
    "beta": "beta",
    "free_cash_flow": "freeCashflow",
    "total_debt": "totalDebt",
    "debt_to_equity": "debtToEquity",
    "current_ratio": "currentRatio",
    "cash_and_equivalents": "totalCash",
}

REQUIRED_INVESTOR_FIELDS = (
    "pe_ratio",
    "roe",
    "dividend_yield",
)


def _cache_file(symbol: str) -> Path:
    safe_symbol = symbol.upper().replace("/", "_")
    return CACHE_DIR / f"{safe_symbol}.json"


def _cache_is_valid(symbol: str) -> bool:
    path = _cache_file(symbol)

    if not path.exists():
        return False

    age_seconds = time.time() - path.stat().st_mtime
    return age_seconds < YAHOO_FUNDAMENTAL_CACHE_HOURS * 3600


def _load_cache(symbol: str):
    with open(_cache_file(symbol), "r", encoding="utf-8") as f:
        data = json.load(f)

    data["cache_status"] = "HIT"
    return data


def _save_cache(symbol: str, data: dict):
    with open(_cache_file(symbol), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _to_float(value):
    if value is None or value == "":
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_debt_to_equity(value):
    debt_to_equity = _to_float(value)

    if debt_to_equity is None:
        return None

    # Yahoo commonly exposes debtToEquity as percent-like units.
    if abs(debt_to_equity) > 10:
        return debt_to_equity / 100

    return debt_to_equity


def _normalize_dividend_yield(value):
    dividend_yield = _to_float(value)

    if dividend_yield is None:
        return None

    # yfinance versions differ: some return 0.012, others return 1.2.
    if abs(dividend_yield) > 0.2:
        return dividend_yield / 100

    return dividend_yield


def _get_ticker_info(symbol: str) -> dict:
    import yfinance as yf

    ticker = yf.Ticker(symbol)

    if hasattr(ticker, "get_info"):
        info = ticker.get_info()
    else:
        info = ticker.info

    return info if isinstance(info, dict) else {}


def _has_required_fields(data: dict) -> bool:
    return any(data.get(field) is not None for field in REQUIRED_INVESTOR_FIELDS)


def _raw_subset(info: dict) -> dict:
    keys = set(YAHOO_FIELD_MAP.values())
    return {key: info.get(key) for key in sorted(keys) if key in info}


def collect_yahoo_fundamentals(symbol: str):
    symbol = symbol.strip().upper()

    if _cache_is_valid(symbol):
        cached = _load_cache(symbol)
        if (
            cached.get("status") == "OK"
            and cached.get("cache_version") == CACHE_VERSION
            and _has_required_fields(cached)
        ):
            return cached

    try:
        info = _get_ticker_info(symbol)

        if not info:
            return {
                "status": "ERROR",
                "symbol": symbol,
                "source": "YAHOO",
                "reason": "Yahoo returned no fundamentals data.",
            }

        result = {
            "status": "OK",
            "cache_status": "MISS",
            "cache_version": CACHE_VERSION,
            "source": "YAHOO",
            "symbol": symbol,
        }

        for target_field, yahoo_key in YAHOO_FIELD_MAP.items():
            value = info.get(yahoo_key)
            if target_field == "debt_to_equity":
                result[target_field] = _normalize_debt_to_equity(value)
            elif target_field == "dividend_yield":
                result[target_field] = _normalize_dividend_yield(value)
            elif target_field in {"sector", "industry"}:
                result[target_field] = value or None
            else:
                result[target_field] = _to_float(value)

        result["provider_fields"] = {
            field: "YAHOO"
            for field in YAHOO_FIELD_MAP
            if result.get(field) is not None
        }
        result["raw_provider_data"] = {
            "info_subset": _raw_subset(info),
        }

        if not _has_required_fields(result):
            return {
                "status": "ERROR",
                "symbol": symbol,
                "source": "YAHOO",
                "reason": "Yahoo fundamentals missing required investor fields.",
                "raw_provider_data": result["raw_provider_data"],
            }

        _save_cache(symbol, result)

        return result

    except Exception as e:
        return {
            "status": "ERROR",
            "symbol": symbol,
            "source": "YAHOO",
            "reason": str(e),
        }
