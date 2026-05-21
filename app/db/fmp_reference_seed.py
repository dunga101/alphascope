import os
from datetime import date
from dotenv import load_dotenv
import psycopg2
import requests

load_dotenv()

API_KEY = os.getenv("FMP_API_KEY")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DB_CONFIG = {
    "host": "192.168.4.124",
    "database": "alphascope",
    "user": "alphascope_app",
    "password": DB_PASSWORD,
    "port": 5432
}

EQUITIES = [
    "BAC",
    "GS",
    "JNJ",
    "ABBV",
    "WMT",
    "COST",
    "AMD",
    "ORCL",
    "CAT",
    "CVX",
    "LMT",
    "RTX"
]

ETFS = [
    "SPY",
    "QQQ",
    "DIA",
    "IWM",
    "XLK",
    "XLF",
    "XLV",
    "XLE",
    "XLI",
    "XLY",
    "XLP",
    "XLU",
    "XLB",
    "XLRE",
    "TLT",
    "GLD",
    "USO"
]

PROFILE_URL = "https://financialmodelingprep.com/stable/profile"
INCOME_URL = "https://financialmodelingprep.com/stable/income-statement"
BALANCE_URL = "https://financialmodelingprep.com/stable/balance-sheet-statement"
CASHFLOW_URL = "https://financialmodelingprep.com/stable/cash-flow-statement"
RATIOS_URL = "https://financialmodelingprep.com/stable/ratios-ttm"


def db_connect():
    return psycopg2.connect(**DB_CONFIG)


def get_json(url, symbol):
    response = requests.get(
        url,
        params={
            "symbol": symbol,
            "apikey": API_KEY
        },
        timeout=20
    )

    response.raise_for_status()
    return response.json()


def upsert_profile(conn, symbol):
    data = get_json(PROFILE_URL, symbol)

    if not data:
        print(f"No profile returned for {symbol}")
        return

    profile = data[0]

    sql = """
    INSERT INTO company_profiles
    (
        symbol,
        company_name,
        sector,
        industry,
        exchange,
        market_cap,
        beta,
        ceo,
        employees,
        description,
        source,
        updated_at
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'FMP',NOW())
    ON CONFLICT (symbol)
    DO UPDATE SET
        company_name = EXCLUDED.company_name,
        sector = EXCLUDED.sector,
        industry = EXCLUDED.industry,
        exchange = EXCLUDED.exchange,
        market_cap = EXCLUDED.market_cap,
        beta = EXCLUDED.beta,
        ceo = EXCLUDED.ceo,
        employees = EXCLUDED.employees,
        description = EXCLUDED.description,
        updated_at = NOW();
    """

    values = (
        symbol,
        profile.get("companyName"),
        profile.get("sector"),
        profile.get("industry"),
        profile.get("exchangeShortName"),
        profile.get("mktCap"),
        profile.get("beta"),
        profile.get("ceo"),
        profile.get("fullTimeEmployees"),
        profile.get("description")
    )

    with conn.cursor() as cur:
        cur.execute(sql, values)

    conn.commit()
    print(f"Profile loaded: {symbol}")


def insert_fundamentals(conn, symbol):
    income = get_json(INCOME_URL, symbol)
    balance = get_json(BALANCE_URL, symbol)
    cashflow = get_json(CASHFLOW_URL, symbol)
    ratios = get_json(RATIOS_URL, symbol)

    if not income or not balance or not cashflow or not ratios:
        print(f"Incomplete fundamentals for {symbol}")
        return

    income_data = income[0]
    balance_data = balance[0]
    cashflow_data = cashflow[0]
    ratios_data = ratios[0]

    sql = """
    INSERT INTO fundamental_snapshots
    (
        symbol,
        snapshot_date,
        revenue,
        net_income,
        total_assets,
        total_liabilities,
        cash_and_equivalents,
        total_debt,
        operating_cash_flow,
        free_cash_flow,
        pe_ratio,
        eps,
        roe,
        debt_to_equity,
        source
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'FMP')
    ON CONFLICT (symbol, snapshot_date)
    DO NOTHING;
    """

    values = (
        symbol,
        date.today(),
        income_data.get("revenue"),
        income_data.get("netIncome"),
        balance_data.get("totalAssets"),
        balance_data.get("totalLiabilities"),
        balance_data.get("cashAndCashEquivalents"),
        balance_data.get("totalDebt"),
        cashflow_data.get("operatingCashFlow"),
        cashflow_data.get("freeCashFlow"),
        ratios_data.get("priceEarningsRatioTTM"),
        ratios_data.get("netIncomePerShareTTM"),
        ratios_data.get("returnOnEquityTTM"),
        ratios_data.get("debtEquityRatioTTM")
    )

    with conn.cursor() as cur:
        cur.execute(sql, values)

    conn.commit()
    print(f"Fundamentals loaded: {symbol}")


def process_equities(conn):
    for symbol in EQUITIES:
        try:
            upsert_profile(conn, symbol)
        except Exception as e:
            print(f"Profile failed for {symbol}: {e}")

        try:
            insert_fundamentals(conn, symbol)
        except Exception as e:
            print(f"Fundamentals failed for {symbol}: {e}")


def process_etfs(conn):
    for symbol in ETFS:
        try:
            upsert_profile(conn, symbol)
        except Exception as e:
            print(f"ETF profile failed for {symbol}: {e}")


def main():
    if not API_KEY:
        raise ValueError("FMP_API_KEY missing")

    if not DB_PASSWORD:
        raise ValueError("DB_PASSWORD missing")

    conn = db_connect()

    try:
        print("=== Loading equity intelligence ===")
        process_equities(conn)

        #print("\n=== Loading ETF metadata ===")
        #process_etfs(conn)

        print("\nSeed operation complete.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
