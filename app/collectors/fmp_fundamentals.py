import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FMP_API_KEY")

PROFILE_URL = "https://financialmodelingprep.com/stable/profile"
INCOME_URL = "https://financialmodelingprep.com/stable/income-statement"
BALANCE_URL = "https://financialmodelingprep.com/stable/balance-sheet-statement"
CASHFLOW_URL = "https://financialmodelingprep.com/stable/cash-flow-statement"
RATIOS_TTM_URL = "https://financialmodelingprep.com/stable/ratios-ttm"


def collect_fundamentals(symbol: str):
    """
    Collect rich fundamental intelligence for AlphaScope.

    Sources:
    - profile
    - income statement
    - balance sheet
    - cash flow
    - ratios TTM
    """

    if not API_KEY:
        return {
            "status": "ERROR",
            "reason": "Missing FMP_API_KEY"
        }

    try:
        urls = {
            "profile": f"{PROFILE_URL}?symbol={symbol}&apikey={API_KEY}",
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

        if not responses["profile"]:
            return {
                "status": "EMPTY",
                "symbol": symbol
            }

        profile = responses["profile"][0]
        income = responses["income"][0] if responses["income"] else {}
        balance = responses["balance"][0] if responses["balance"] else {}
        cashflow = responses["cashflow"][0] if responses["cashflow"] else {}
        ratios = responses["ratios"][0] if responses["ratios"] else {}

        return {
            "status": "OK",
            "symbol": symbol,

            # profile / valuation
            "company_name": profile.get("companyName"),
            "market_cap": profile.get("marketCap"),
            "price": profile.get("price"),
            "beta": profile.get("beta"),

            # valuation
            "pe_ratio": ratios.get("priceEarningsRatioTTM"),
            "price_to_book": ratios.get("priceToBookRatioTTM"),
            "earnings_yield": ratios.get("earningsYieldTTM"),

            # profitability
            "gross_margin": ratios.get("grossProfitMarginTTM"),
            "operating_margin": ratios.get("operatingProfitMarginTTM"),
            "net_margin": ratios.get("netProfitMarginTTM"),
            "roe": ratios.get("returnOnEquityTTM"),

            # balance sheet
            "debt_to_equity": ratios.get("debtEquityRatioTTM"),
            "current_ratio": ratios.get("currentRatioTTM"),
            "cash_and_equivalents": balance.get("cashAndCashEquivalents"),
            "total_debt": balance.get("totalDebt"),

            # income statement
            "revenue": income.get("revenue"),
            "net_income": income.get("netIncome"),

            # cash flow
            "operating_cash_flow": cashflow.get("operatingCashFlow"),
            "free_cash_flow": cashflow.get("freeCashFlow"),
            "capital_expenditure": cashflow.get("capitalExpenditure"),
        }

    except Exception as e:
        return {
            "status": "ERROR",
            "symbol": symbol,
            "reason": str(e)
        }