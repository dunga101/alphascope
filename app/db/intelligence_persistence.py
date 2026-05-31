import json
import os
from datetime import date

import psycopg2
from dotenv import load_dotenv

try:
    from psycopg2.extras import RealDictCursor
except ImportError:
    RealDictCursor = None

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "5432")


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
    )


def persist_intelligence_report(ai_output: dict):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO intelligence_reports (
            report_date,
            market_regime,
            confidence_score,
            quick_take,
            executive_summary,
            recommended_posture,
            bullish_signals,
            bearish_signals,
            risk_flags,
            raw_ai_output
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_date)
        DO UPDATE SET
            market_regime = EXCLUDED.market_regime,
            confidence_score = EXCLUDED.confidence_score,
            quick_take = EXCLUDED.quick_take,
            executive_summary = EXCLUDED.executive_summary,
            recommended_posture = EXCLUDED.recommended_posture,
            bullish_signals = EXCLUDED.bullish_signals,
            bearish_signals = EXCLUDED.bearish_signals,
            risk_flags = EXCLUDED.risk_flags,
            raw_ai_output = EXCLUDED.raw_ai_output;
        """,
        (
            date.today(),
            ai_output.get("market_regime", "MIXED"),
            ai_output.get("confidence", 50),
            ai_output.get("quick_take"),
            ai_output.get("executive_summary"),
            ai_output.get("recommended_posture"),
            json.dumps(ai_output.get("bullish_signals", [])),
            json.dumps(ai_output.get("bearish_signals", [])),
            json.dumps(ai_output.get("risk_flags", [])),
            json.dumps(ai_output),
        ),
    )

    conn.commit()
    cur.close()
    conn.close()


def persist_event_snapshot(event_output: dict):
    conn = get_connection()
    cur = conn.cursor()

    event_regime = (
        event_output.get("event_regime")
        or event_output.get("market_regime_bias")
        or "MIXED"
    )

    event_confidence = (
        event_output.get("event_confidence")
        or event_output.get("confidence")
        or 50
    )

    major_headlines = (
        event_output.get("major_headlines")
        or event_output.get("headlines")
        or event_output.get("key_catalysts")
        or []
    )

    cur.execute(
        """
        INSERT INTO event_snapshots (
            report_date,
            event_regime,
            event_confidence,
            major_headlines,
            bullish_events,
            bearish_events,
            neutral_events,
            risk_events,
            raw_event_output
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_date)
        DO UPDATE SET
            event_regime = EXCLUDED.event_regime,
            event_confidence = EXCLUDED.event_confidence,
            major_headlines = EXCLUDED.major_headlines,
            bullish_events = EXCLUDED.bullish_events,
            bearish_events = EXCLUDED.bearish_events,
            neutral_events = EXCLUDED.neutral_events,
            risk_events = EXCLUDED.risk_events,
            raw_event_output = EXCLUDED.raw_event_output;
        """,
        (
            date.today(),
            event_regime,
            event_confidence,
            json.dumps(major_headlines),
            json.dumps(event_output.get("bullish_events", [])),
            json.dumps(event_output.get("bearish_events", [])),
            json.dumps(event_output.get("neutral_events", [])),
            json.dumps(event_output.get("risk_events", [])),
            json.dumps(event_output),
        ),
    )

    conn.commit()
    cur.close()
    conn.close()


def persist_fundamental_snapshot(symbol: str, fundamentals: dict):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO fundamental_snapshots (
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
            dividend_yield,
            source
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'FMP')
        ON CONFLICT (symbol, snapshot_date)
        DO UPDATE SET
            revenue = EXCLUDED.revenue,
            net_income = EXCLUDED.net_income,
            total_assets = EXCLUDED.total_assets,
            total_liabilities = EXCLUDED.total_liabilities,
            cash_and_equivalents = EXCLUDED.cash_and_equivalents,
            total_debt = EXCLUDED.total_debt,
            operating_cash_flow = EXCLUDED.operating_cash_flow,
            free_cash_flow = EXCLUDED.free_cash_flow,
            pe_ratio = EXCLUDED.pe_ratio,
            eps = EXCLUDED.eps,
            roe = EXCLUDED.roe,
            debt_to_equity = EXCLUDED.debt_to_equity,
            dividend_yield = EXCLUDED.dividend_yield,
            source = EXCLUDED.source;
        """,
        (
            symbol.upper(),
            date.today(),
            fundamentals.get("revenue"),
            fundamentals.get("net_income"),
            fundamentals.get("total_assets"),
            fundamentals.get("total_liabilities"),
            fundamentals.get("cash_and_equivalents"),
            fundamentals.get("total_debt"),
            fundamentals.get("operating_cash_flow"),
            fundamentals.get("free_cash_flow"),
            fundamentals.get("pe_ratio"),
            fundamentals.get("eps"),
            fundamentals.get("roe"),
            fundamentals.get("debt_to_equity"),
            fundamentals.get("dividend_yield"),
        ),
    )

    conn.commit()
    cur.close()
    conn.close()


def persist_investor_score(score: dict):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO investor_scores (
            score_date,
            symbol,
            company_name,
            sector,
            buy_score,
            recommendation,
            valuation_score,
            dividend_score,
            financial_quality_score,
            price_position_score,
            technical_score,
            dividend_yield,
            pe_ratio,
            distance_from_52w_low,
            rsi,
            raw_score
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (score_date, symbol)
        DO UPDATE SET
            company_name = EXCLUDED.company_name,
            sector = EXCLUDED.sector,
            buy_score = EXCLUDED.buy_score,
            recommendation = EXCLUDED.recommendation,
            valuation_score = EXCLUDED.valuation_score,
            dividend_score = EXCLUDED.dividend_score,
            financial_quality_score = EXCLUDED.financial_quality_score,
            price_position_score = EXCLUDED.price_position_score,
            technical_score = EXCLUDED.technical_score,
            dividend_yield = EXCLUDED.dividend_yield,
            pe_ratio = EXCLUDED.pe_ratio,
            distance_from_52w_low = EXCLUDED.distance_from_52w_low,
            rsi = EXCLUDED.rsi,
            raw_score = EXCLUDED.raw_score;
        """,
        (
            date.today(),
            score.get("symbol"),
            score.get("company"),
            score.get("sector"),
            score.get("buy_score"),
            score.get("recommendation"),
            score.get("valuation_score"),
            score.get("dividend_score"),
            score.get("financial_quality_score"),
            score.get("price_position_score"),
            score.get("technical_score"),
            score.get("dividend_yield"),
            score.get("pe_ratio"),
            score.get("distance_from_52w_low"),
            score.get("rsi"),
            json.dumps(score.get("raw_score", {})),
        ),
    )

    conn.commit()
    cur.close()
    conn.close()


def persist_investor_scores(scores: list[dict]):
    for score in scores:
        persist_investor_score(score)


def fetch_latest_investor_rankings() -> list[dict]:
    conn = get_connection()
    if RealDictCursor is None:
        cur = conn.cursor()
    else:
        cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        WITH latest_scores AS (
            SELECT MAX(score_date) AS score_date
            FROM investor_scores
        )
        SELECT
            ROW_NUMBER() OVER (ORDER BY scores.buy_score DESC) AS rank,
            scores.score_date,
            scores.symbol,
            scores.company_name,
            scores.sector,
            scores.buy_score,
            scores.recommendation,
            scores.valuation_score,
            scores.dividend_score,
            scores.financial_quality_score,
            scores.price_position_score,
            scores.technical_score,
            scores.dividend_yield,
            scores.pe_ratio,
            scores.distance_from_52w_low,
            scores.rsi,
            scores.raw_score,
            fundamentals.roe,
            fundamentals.debt_to_equity,
            fundamentals.free_cash_flow,
            technicals.raw_signals AS technical_raw_signals
        FROM investor_scores scores
        JOIN latest_scores latest
            ON scores.score_date = latest.score_date
        LEFT JOIN LATERAL (
            SELECT
                roe,
                debt_to_equity,
                free_cash_flow
            FROM fundamental_snapshots
            WHERE symbol = scores.symbol
            ORDER BY snapshot_date DESC
            LIMIT 1
        ) fundamentals ON TRUE
        LEFT JOIN LATERAL (
            SELECT raw_signals
            FROM technical_snapshots
            WHERE symbol = scores.symbol
            ORDER BY report_date DESC
            LIMIT 1
        ) technicals ON TRUE
        ORDER BY scores.buy_score DESC;
        """
    )

    fetched = cur.fetchall()

    if RealDictCursor is None:
        columns = [column[0] for column in cur.description]
        rows = [dict(zip(columns, row)) for row in fetched]
    else:
        rows = [dict(row) for row in fetched]

    cur.close()
    conn.close()

    return rows


def persist_technical_snapshot(symbol: str, technical_output: dict):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO technical_snapshots (
            report_date,
            symbol,
            signal_score,
            trend_score,
            momentum_score,
            volatility_score,
            risk_score,
            technical_regime,
            technical_confidence,
            raw_signals
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_date, symbol)
        DO UPDATE SET
            signal_score = EXCLUDED.signal_score,
            trend_score = EXCLUDED.trend_score,
            momentum_score = EXCLUDED.momentum_score,
            volatility_score = EXCLUDED.volatility_score,
            risk_score = EXCLUDED.risk_score,
            technical_regime = EXCLUDED.technical_regime,
            technical_confidence = EXCLUDED.technical_confidence,
            raw_signals = EXCLUDED.raw_signals;
        """,
        (
            date.today(),
            symbol,
            technical_output.get("signal_score"),
            technical_output.get("trend_score"),
            technical_output.get("momentum_score"),
            technical_output.get("volatility_score"),
            technical_output.get("risk_score"),
            technical_output.get("technical_regime"),
            technical_output.get("technical_confidence"),
            json.dumps(technical_output),
        ),
    )

    conn.commit()
    cur.close()
    conn.close()
