# app/collectors/fmp_profile.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FMP_API_KEY")
BASE_URL = "https://financialmodelingprep.com/stable/profile"


def collect_company_profile(symbol: str):

    if not API_KEY:
        return {
            "status": "ERROR",
            "reason": "Missing FMP_API_KEY"
        }

    url = f"{BASE_URL}?symbol={symbol}&apikey={API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        if not data:
            return {
                "status": "EMPTY",
                "symbol": symbol
            }

        profile = data[0]

        return {
            "status": "OK",
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
            "ceo": profile.get("ceo")
        }

    except Exception as e:
        return {
            "status": "ERROR",
            "symbol": symbol,
            "reason": str(e)
        }