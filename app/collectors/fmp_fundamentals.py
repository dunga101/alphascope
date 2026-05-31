import os
import json
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FMP_API_KEY")

INCOME_URL = "https://financialmodelingprep.com/stable/income-statement"
BALANCE_URL = "https://financialmodelingprep.com/stable/balance-sheet-statement"
CASHFLOW_URL = "https://financialmodelingprep.com/stable/cash-flow-statement"
RATIOS_TTM_URL = "https://financialmodelingprep.com/stable/ratios-ttm"

CACHE_DIR = Path("data/cache/fmp_fundamentals")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

FUNDAMENTAL_CACHE_HOURS = int(
    os.getenv("FMP_FUNDAMENTAL_CACHE_HOURS", "24")
)


def _cache_file(symbol: str) -> Path:
    safe_symbol = symbol.upper().replace("/", "_")
    return CACHE_DIR / f"{safe_symbol}.json"


def _cache_is_valid(symbol: str) -> bool:
    path = _cache_file(symbol)

    if not path.exists():
        return False

    age_seconds = time.time() - path.stat().st_mtime
    return age_seconds < FUNDAMENTAL_CACHE_HOURS * 3600


def _load_cache(symbol: str):
    with open(_cache_file(symbol), "r", encoding="utf-8") as f:
        data = json.load(f)

    data["cache_status"] = "HIT"
    return data


def _save_cache(symbol: str, data: dict):
    with open(_cache_file(symbol), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _calculate_roe(net_income, total_stockholders_equity):
    if net_income is None or total_stockholders_equity in (None, 0):
        return None

    return net_income / total_stockholders_equity


def collect_fundamentals(symbol: str):
    symbol = symbol.strip().upper()

    if not API_KEY:
        return {
            "status": "ERROR",
            "reason": "Missing FMP_API_KEY",
        }

    if _cache_is_valid(symbol):
        return _load_cache(symbol)

    try:
        urls = {
            "income": f"{INCOME_URL}?symbol={symbol}&apikey={API_KEY}",
            "balance": f"{BALANCE_URL}?symbol={symbol}&apikey={API_KEY}",
            "cashflow": f"{CASHFLOW_URL}?symbol={symbol}&apikey={API_KEY}",
            "ratios": f"{RATIOS_TTM_URL}?symbol={symbol}&apikey={API_KEY}",
        }

        responses = {}

        for key, url in urls.items():
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            responses[key] = r.json()

        income = responses["income"][0] if responses["income"] else {}
        balance = responses["balance"][0] if responses["balance"] else {}
        cashflow = responses["cashflow"][0] if responses["cashflow"] else {}
        ratios = responses["ratios"][0] if responses["ratios"] else {}
        roe = _calculate_roe(
            income.get("netIncome"),
            balance.get("totalStockholdersEquity"),
        )

        result = {
            "status": "OK",
            "cache_status": "MISS",
            "symbol": symbol,

            "pe_ratio": ratios.get("priceToEarningsRatioTTM"),
            "price_to_book": ratios.get("priceToBookRatioTTM"),
            "earnings_yield": ratios.get("earningsYieldTTM"),

            "gross_margin": ratios.get("grossProfitMarginTTM"),
            "operating_margin": ratios.get("operatingProfitMarginTTM"),
            "net_margin": ratios.get("netProfitMarginTTM"),
            "roe": roe,

            "debt_to_equity": ratios.get("debtToEquityRatioTTM"),
            "current_ratio": ratios.get("currentRatioTTM"),
            "cash_and_equivalents": balance.get("cashAndCashEquivalents"),
            "total_debt": balance.get("totalDebt"),

            "revenue": income.get("revenue"),
            "net_income": income.get("netIncome"),

            "operating_cash_flow": cashflow.get("operatingCashFlow"),
            "free_cash_flow": cashflow.get("freeCashFlow"),
            "capital_expenditure": cashflow.get("capitalExpenditure"),
        }

        _save_cache(symbol, result)

        return result

    except Exception as e:
        return {
            "status": "ERROR",
            "symbol": symbol,
            "reason": str(e),
        }
