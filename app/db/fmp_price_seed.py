import os
from dotenv import load_dotenv
import psycopg2
import requests
from psycopg2.extras import execute_batch

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

SYMBOLS = [
    "SPY",

    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "META",
    "GOOGL",
    "TSLA",
    "JPM",
    "XOM",
    "UNH",
    "BAC",
    "GS",
    "JNJ",
    "WMT",
    "AMD",
    "CVX"
]

HISTORICAL_URL = "https://financialmodelingprep.com/stable/historical-price-eod/full"


def db_connect():
    return psycopg2.connect(**DB_CONFIG)


def fetch_prices(symbol):
    response = requests.get(
        HISTORICAL_URL,
        params={
            "symbol": symbol,
            "apikey": API_KEY
        },
        timeout=30
    )

    response.raise_for_status()
    data = response.json()

    if not data:
        return []

    rows = []

    for item in data:
        rows.append((
            item["symbol"],
            item["date"],
            item.get("open"),
            item.get("high"),
            item.get("low"),
            item.get("close"),
            item.get("volume"),
            "FMP"
        ))

    return rows


def insert_prices(conn, rows):
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
    if not API_KEY:
        raise ValueError("FMP_API_KEY missing")

    if not DB_PASSWORD:
        raise ValueError("DB_PASSWORD missing")

    conn = db_connect()

    try:
        for symbol in SYMBOLS:
            try:
                print(f"Fetching {symbol}...")

                rows = fetch_prices(symbol)

                if rows:
                    insert_prices(conn, rows)
                    print(f"Inserted {len(rows)} rows for {symbol}")
                else:
                    print(f"No historical data for {symbol}")

            except Exception as e:
                print(f"Skipping {symbol}: {e}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()