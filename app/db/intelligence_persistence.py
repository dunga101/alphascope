import json
import os
from datetime import date

import psycopg2
from dotenv import load_dotenv

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
            source
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'FMP')
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
        ),
    )

    conn.commit()
    cur.close()
    conn.close()


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
