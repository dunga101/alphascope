# app/collectors/fmp_profile.py

import os
import json
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FMP_API_KEY")
BASE_URL = "https://financialmodelingprep.com/stable/profile"

CACHE_DIR = Path("data/cache/fmp_profiles")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

PROFILE_CACHE_HOURS = int(os.getenv("FMP_PROFILE_CACHE_HOURS", "168"))


def _cache_file(symbol: str) -> Path:
    safe_symbol = symbol.upper().replace("/", "_")
    return CACHE_DIR / f"{safe_symbol}.json"


def _cache_is_valid(symbol: str) -> bool:
    path = _cache_file(symbol)

    if not path.exists():
        return False

    age_seconds = time.time() - path.stat().st_mtime
    return age_seconds < PROFILE_CACHE_HOURS * 3600


def _load_cache(symbol: str):
    with open(_cache_file(symbol), "r", encoding="utf-8") as f:
        data = json.load(f)

    data["cache_status"] = "HIT"
    return data


def _save_cache(symbol: str, data: dict) -> None:
    with open(_cache_file(symbol), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def collect_company_profile(symbol: str):
    symbol = symbol.strip().upper()

    if not API_KEY:
        return {
            "status": "ERROR",
            "symbol": symbol,
            "reason": "Missing FMP_API_KEY",
        }

    if _cache_is_valid(symbol):
        return _load_cache(symbol)

    url = f"{BASE_URL}?symbol={symbol}&apikey={API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        if not data:
            return {
                "status": "EMPTY",
                "symbol": symbol,
            }

        profile = data[0]

        result = {
            "status": "OK",
            "cache_status": "MISS",
            "symbol": symbol,
            "company_name": profile.get("companyName"),
            "sector": profile.get("sector"),
            "industry": profile.get("industry"),
            "market_cap": profile.get("marketCap"),
            "beta": profile.get("beta"),
            "price": profile.get("price"),
            "exchange": profile.get("exchangeShortName"),
            "country": profile.get("country"),
            "description": profile.get("description"),
            "website": profile.get("website"),
            "ceo": profile.get("ceo"),
        }

        _save_cache(symbol, result)
        return result

    except Exception as e:
        return {
            "status": "ERROR",
            "symbol": symbol,
            "reason": str(e),
        }