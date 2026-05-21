import os
from dataclasses import dataclass
from typing import Optional, Dict, Any

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


@dataclass
class TechnicalIndicators:
    symbol: str
    latest_date: str
    latest_close: float
    sma20: Optional[float]
    sma50: Optional[float]
    sma200: Optional[float]
    rsi14: Optional[float]
    atr14: Optional[float]
    volatility30d: Optional[float]
    drawdown_from_52w_high_pct: Optional[float]
    distance_from_52w_low_pct: Optional[float]
    relative_strength_vs_spy_90d: Optional[float]


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def fetch_price_history(symbol: str, limit: int = 300) -> pd.DataFrame:
    query = """
        SELECT
            symbol,
            trade_date AS price_date,
            open,
            high,
            low,
            close,
            volume
        FROM market_prices
        WHERE symbol = %s
        ORDER BY trade_date DESC
        LIMIT %s;
    """

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (symbol.upper(), limit))
            rows = cur.fetchall()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.sort_values("price_date").reset_index(drop=True)

    numeric_cols = ["open", "high", "low", "close", "volume"]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def calculate_sma(df: pd.DataFrame, window: int) -> Optional[float]:
    if len(df) < window:
        return None

    sma = df["close"].rolling(window).mean().iloc[-1]
    return round(float(sma), 2)


def calculate_rsi(df: pd.DataFrame, window: int = 14) -> Optional[float]:
    if len(df) < window + 1:
        return None

    delta = df["close"].diff()

    gains = delta.where(delta > 0, 0.0)
    losses = -delta.where(delta < 0, 0.0)

    avg_gain = gains.rolling(window=window).mean()
    avg_loss = losses.rolling(window=window).mean()

    latest_loss = avg_loss.iloc[-1]

    if pd.isna(latest_loss):
        return None

    if latest_loss == 0:
        return 100.0

    rs = avg_gain.iloc[-1] / latest_loss
    rsi = 100 - (100 / (1 + rs))

    return round(float(rsi), 2)


def calculate_atr(df: pd.DataFrame, window: int = 14) -> Optional[float]:
    if len(df) < window + 1:
        return None

    high_low = df["high"] - df["low"]
    high_prev_close = (df["high"] - df["close"].shift(1)).abs()
    low_prev_close = (df["low"] - df["close"].shift(1)).abs()

    true_range = pd.concat(
        [high_low, high_prev_close, low_prev_close],
        axis=1
    ).max(axis=1)

    atr = true_range.rolling(window=window).mean().iloc[-1]

    if pd.isna(atr):
        return None

    return round(float(atr), 2)


def calculate_volatility(df: pd.DataFrame, window: int = 30) -> Optional[float]:
    if len(df) < window + 1:
        return None

    returns = df["close"].pct_change()
    volatility = returns.rolling(window=window).std().iloc[-1] * (252 ** 0.5)

    if pd.isna(volatility):
        return None

    return round(float(volatility * 100), 2)


def calculate_52w_position(df: pd.DataFrame) -> Dict[str, Optional[float]]:
    if len(df) < 30:
        return {
            "drawdown_from_52w_high_pct": None,
            "distance_from_52w_low_pct": None,
        }

    lookback = min(len(df), 252)
    recent = df.tail(lookback)

    latest_close = float(recent["close"].iloc[-1])
    high_52w = float(recent["close"].max())
    low_52w = float(recent["close"].min())

    if high_52w == 0 or low_52w == 0:
        return {
            "drawdown_from_52w_high_pct": None,
            "distance_from_52w_low_pct": None,
        }

    drawdown = ((latest_close - high_52w) / high_52w) * 100
    distance_low = ((latest_close - low_52w) / low_52w) * 100

    return {
        "drawdown_from_52w_high_pct": round(drawdown, 2),
        "distance_from_52w_low_pct": round(distance_low, 2),
    }


def calculate_relative_strength(
    symbol_df: pd.DataFrame,
    spy_df: pd.DataFrame,
    window: int = 90
) -> Optional[float]:
    if len(symbol_df) < window or len(spy_df) < window:
        return None

    symbol_slice = symbol_df.tail(window)
    spy_slice = spy_df.tail(window)

    symbol_start = float(symbol_slice["close"].iloc[0])
    symbol_end = float(symbol_slice["close"].iloc[-1])

    spy_start = float(spy_slice["close"].iloc[0])
    spy_end = float(spy_slice["close"].iloc[-1])

    if symbol_start == 0 or spy_start == 0:
        return None

    symbol_return = (symbol_end - symbol_start) / symbol_start
    spy_return = (spy_end - spy_start) / spy_start

    rs = (symbol_return - spy_return) * 100

    return round(float(rs), 2)


def get_symbol_indicators(symbol: str) -> Optional[TechnicalIndicators]:
    symbol = symbol.upper()

    df = fetch_price_history(symbol)

    if df.empty:
        print(f"No price history found for {symbol}")
        return None

    spy_df = fetch_price_history("SPY")

    latest = df.iloc[-1]
    position = calculate_52w_position(df)

    rs_vs_spy = None
    if symbol != "SPY" and not spy_df.empty:
        rs_vs_spy = calculate_relative_strength(df, spy_df)

    return TechnicalIndicators(
        symbol=symbol,
        latest_date=str(latest["price_date"]),
        latest_close=round(float(latest["close"]), 2),
        sma20=calculate_sma(df, 20),
        sma50=calculate_sma(df, 50),
        sma200=calculate_sma(df, 200),
        rsi14=calculate_rsi(df, 14),
        atr14=calculate_atr(df, 14),
        volatility30d=calculate_volatility(df, 30),
        drawdown_from_52w_high_pct=position["drawdown_from_52w_high_pct"],
        distance_from_52w_low_pct=position["distance_from_52w_low_pct"],
        relative_strength_vs_spy_90d=rs_vs_spy,
    )


def indicators_to_dict(indicators: TechnicalIndicators) -> Dict[str, Any]:
    return {
        "symbol": indicators.symbol,
        "latest_date": indicators.latest_date,
        "latest_close": indicators.latest_close,
        "sma20": indicators.sma20,
        "sma50": indicators.sma50,
        "sma200": indicators.sma200,
        "rsi14": indicators.rsi14,
        "atr14": indicators.atr14,
        "volatility30d_pct": indicators.volatility30d,
        "drawdown_from_52w_high_pct": indicators.drawdown_from_52w_high_pct,
        "distance_from_52w_low_pct": indicators.distance_from_52w_low_pct,
        "relative_strength_vs_spy_90d_pct": indicators.relative_strength_vs_spy_90d,
    }


def print_symbol_report(symbol: str):
    indicators = get_symbol_indicators(symbol)

    if indicators is None:
        return

    report = indicators_to_dict(indicators)

    print("\n" + "=" * 60)
    print(f"TECHNICAL INDICATOR REPORT: {symbol}")
    print("=" * 60)

    for key, value in report.items():
        print(f"{key}: {value}")


def main():
    test_symbols = ["SPY", "QQQ", "NVDA", "TSLA"]

    for symbol in test_symbols:
        print_symbol_report(symbol)


if __name__ == "__main__":
    main()