import os
import requests
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_batch

load_dotenv()

FMP_API_KEY = os.getenv("FMP_API_KEY")

DB_CONFIG = {
    "host": "192.168.4.124",
    "database": "alphascope",
    "user": "alphascope_app",
    "password": os.getenv("DB_PASSWORD"),
    "port": 5432
}

SYMBOLS = [
    "SPY", "QQQ", "DIA", "IWM", "VTI",
    "TLT", "GLD", "USO", "XLE", "VIXY",
    "XLK", "XLF", "XLV", "XLI", "XLY",
    "XLP", "XLU", "XLB", "XLRE",
    "AAPL", "MSFT", "NVDA", "AMZN",
    "META", "GOOGL", "TSLA", "JPM",
    "XOM", "UNH"
]


def db_connect():
    return psycopg2.connect(**DB_CONFIG)


def fetch_historical_prices(symbol):
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?apikey={FMP_API_KEY}"

    print(f"Fetching historical prices for {symbol}...")

    r = requests.get(url, timeout=30)
    r.raise_for_status()

    data = r.json()

    if "historical" not in data:
        print(f"No data returned for {symbol}")
        return []

    rows = []

    for entry in data["historical"]:
        rows.append((
            symbol,
            entry["date"],
            entry.get("open"),
            entry.get("high"),
            entry.get("low"),
            entry.get("close"),
            entry.get("volume"),
            "FMP"
        ))

    return rows


def insert_market_prices(conn, rows):
    sql = """
    INSERT INTO market_prices
    (
        symbol,
        trade_date,
        open,
        high,
        low,
        close,
        volume,
        source
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT (symbol, trade_date)
    DO NOTHING;
    """

    with conn.cursor() as cur:
        execute_batch(cur, sql, rows, page_size=500)

    conn.commit()


def main():
    if not FMP_API_KEY:
        raise ValueError("FMP_API_KEY missing")

    conn = db_connect()

    total_rows = 0

    try:
        for symbol in SYMBOLS:
            rows = fetch_historical_prices(symbol)

            if rows:
                insert_market_prices(conn, rows)
                total_rows += len(rows)
                print(f"Inserted {len(rows)} rows for {symbol}")

        print(f"\nDONE. Total rows processed: {total_rows}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
