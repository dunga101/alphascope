import json
import os
import re
import time
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv(".env")

FRED_API_KEY = os.getenv("FRED_API_KEY")
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
FRED_CACHE_HOURS = int(os.getenv("FRED_CACHE_HOURS", "6"))
FRED_MONTHLY_CACHE_HOURS = int(os.getenv("FRED_MONTHLY_CACHE_HOURS", "12"))

FRED_CACHE_DIR = Path("data/cache/fred")
FRED_CACHE_DIR.mkdir(parents=True, exist_ok=True)

FRED_SERIES = {
    "FEDFUNDS": {
        "name": "Effective Federal Funds Rate",
        "frequency": "monthly",
        "limit": 24,
    },
    "CPIAUCSL": {
        "name": "Consumer Price Index for All Urban Consumers",
        "frequency": "monthly",
        "limit": 36,
    },
    "UNRATE": {
        "name": "Unemployment Rate",
        "frequency": "monthly",
        "limit": 24,
    },
    "DGS10": {
        "name": "10-Year Treasury Constant Maturity Rate",
        "frequency": "daily",
        "limit": 90,
    },
    "DGS2": {
        "name": "2-Year Treasury Constant Maturity Rate",
        "frequency": "daily",
        "limit": 90,
    },
}


def _cache_file(series_id: str) -> Path:
    return FRED_CACHE_DIR / f"{series_id.upper()}.json"


def _cache_ttl_hours(series_id: str) -> int:
    series = FRED_SERIES.get(series_id.upper(), {})
    if series.get("frequency") == "monthly":
        return FRED_MONTHLY_CACHE_HOURS
    return FRED_CACHE_HOURS


def _cache_is_valid(series_id: str) -> bool:
    path = _cache_file(series_id)
    if not path.exists():
        return False

    age_hours = (time.time() - path.stat().st_mtime) / 3600
    return age_hours < _cache_ttl_hours(series_id)


def _load_cache(series_id: str) -> dict:
    with open(_cache_file(series_id), "r", encoding="utf-8") as file:
        data = json.load(file)

    data["cache_status"] = "HIT"
    return data


def _save_cache(series_id: str, data: dict) -> None:
    with open(_cache_file(series_id), "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def _to_float(value: Any):
    if value in (None, "."):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sanitize_error(message: str) -> str:
    return re.sub(r"api_key=[^&\s]+", "api_key=REDACTED", message)


def _normalize_observations(series_id: str, observations: list[dict]) -> list[dict]:
    normalized = []

    for observation in observations:
        normalized.append(
            {
                "series_id": series_id,
                "date": observation.get("date"),
                "value": _to_float(observation.get("value")),
                "realtime_start": observation.get("realtime_start"),
                "realtime_end": observation.get("realtime_end"),
                "raw_observation": observation,
            }
        )

    normalized.sort(key=lambda item: item.get("date") or "")
    return normalized


def _fetch_series(series_id: str) -> dict:
    series_id = series_id.upper()

    if _cache_is_valid(series_id):
        return _load_cache(series_id)

    meta = FRED_SERIES[series_id]
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": meta["limit"],
    }

    response = requests.get(FRED_BASE_URL, params=params, timeout=15)
    response.raise_for_status()
    payload = response.json()
    observations = _normalize_observations(
        series_id,
        payload.get("observations", []),
    )

    result = {
        "series_id": series_id,
        "name": meta["name"],
        "frequency": meta["frequency"],
        "cache_status": "MISS",
        "observations": observations,
        "latest": next(
            (
                observation
                for observation in reversed(observations)
                if observation.get("value") is not None
            ),
            None,
        ),
    }

    _save_cache(series_id, result)
    return result


def collect_fred_macro(series_ids: list[str] | None = None) -> dict:
    series_ids = series_ids or list(FRED_SERIES.keys())

    if not FRED_API_KEY:
        return {
            "status": "ERROR",
            "source": "FRED",
            "series": {},
            "errors": {
                "FRED_API_KEY": "Missing FRED_API_KEY in .env",
            },
            "cache_stats": {
                "hits": 0,
                "misses": 0,
            },
        }

    output = {}
    errors = {}
    cache_stats = {
        "hits": 0,
        "misses": 0,
    }

    for series_id in series_ids:
        series_id = series_id.upper()

        if series_id not in FRED_SERIES:
            errors[series_id] = "Unsupported FRED series"
            continue

        try:
            result = _fetch_series(series_id)
            if result.get("cache_status") == "HIT":
                cache_stats["hits"] += 1
            else:
                cache_stats["misses"] += 1

            output[series_id] = result
        except Exception as exc:
            errors[series_id] = _sanitize_error(str(exc) or repr(exc))

    return {
        "status": "OK" if output else "ERROR",
        "source": "FRED",
        "series": output,
        "errors": errors,
        "cache_stats": cache_stats,
    }
