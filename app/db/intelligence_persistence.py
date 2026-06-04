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
    source = fundamentals.get("source") or fundamentals.get("provider_used") or "UNKNOWN"

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
            source,
            provider_used,
            providers_available,
            pe_ratio_source,
            roe_source,
            dividend_yield_source,
            debt_to_equity_source,
            free_cash_flow_source,
            market_cap,
            market_cap_source,
            sector,
            industry,
            data_completeness_percent,
            available_fields,
            missing_fields,
            provider_errors,
            raw_provider_data
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            source = EXCLUDED.source,
            provider_used = EXCLUDED.provider_used,
            providers_available = EXCLUDED.providers_available,
            pe_ratio_source = EXCLUDED.pe_ratio_source,
            roe_source = EXCLUDED.roe_source,
            dividend_yield_source = EXCLUDED.dividend_yield_source,
            debt_to_equity_source = EXCLUDED.debt_to_equity_source,
            free_cash_flow_source = EXCLUDED.free_cash_flow_source,
            market_cap = EXCLUDED.market_cap,
            market_cap_source = EXCLUDED.market_cap_source,
            sector = EXCLUDED.sector,
            industry = EXCLUDED.industry,
            data_completeness_percent = EXCLUDED.data_completeness_percent,
            available_fields = EXCLUDED.available_fields,
            missing_fields = EXCLUDED.missing_fields,
            provider_errors = EXCLUDED.provider_errors,
            raw_provider_data = EXCLUDED.raw_provider_data;
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
            source,
            fundamentals.get("provider_used") or source,
            json.dumps(fundamentals.get("providers_available", [])),
            fundamentals.get("pe_ratio_source"),
            fundamentals.get("roe_source"),
            fundamentals.get("dividend_yield_source"),
            fundamentals.get("debt_to_equity_source"),
            fundamentals.get("free_cash_flow_source"),
            fundamentals.get("market_cap"),
            fundamentals.get("market_cap_source"),
            fundamentals.get("sector"),
            fundamentals.get("industry"),
            fundamentals.get("data_completeness_percent"),
            json.dumps(fundamentals.get("available_fields", [])),
            json.dumps(fundamentals.get("missing_fields", [])),
            json.dumps(fundamentals.get("provider_errors", {})),
            json.dumps(fundamentals.get("raw_provider_data", {})),
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
            fundamentals.provider_used,
            fundamentals.providers_available,
            fundamentals.pe_ratio_source,
            fundamentals.roe_source,
            fundamentals.dividend_yield_source,
            fundamentals.debt_to_equity_source,
            fundamentals.free_cash_flow_source,
            fundamentals.data_completeness_percent,
            fundamentals.available_fields,
            fundamentals.missing_fields,
            fundamentals.provider_errors,
            technicals.raw_signals AS technical_raw_signals
        FROM investor_scores scores
        JOIN latest_scores latest
            ON scores.score_date = latest.score_date
        LEFT JOIN LATERAL (
            SELECT
                roe,
                debt_to_equity,
                free_cash_flow,
                provider_used,
                providers_available,
                pe_ratio_source,
                roe_source,
                dividend_yield_source,
                debt_to_equity_source,
                free_cash_flow_source,
                data_completeness_percent,
                available_fields,
                missing_fields,
                provider_errors
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


def persist_fred_observations(fred_payload: dict):
    series_map = fred_payload.get("series", {}) if isinstance(fred_payload, dict) else {}
    if not series_map:
        return 0

    conn = get_connection()
    cur = conn.cursor()
    persisted_count = 0

    for series_id, series_data in series_map.items():
        observations = series_data.get("observations", []) if isinstance(series_data, dict) else []

        for observation in observations:
            observation_date = observation.get("date")
            if not observation_date:
                continue

            cur.execute(
                """
                INSERT INTO fred_observations (
                    series_id,
                    observation_date,
                    value,
                    realtime_start,
                    realtime_end,
                    raw_observation
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (series_id, observation_date)
                DO UPDATE SET
                    value = EXCLUDED.value,
                    realtime_start = EXCLUDED.realtime_start,
                    realtime_end = EXCLUDED.realtime_end,
                    raw_observation = EXCLUDED.raw_observation,
                    updated_at = NOW();
                """,
                (
                    series_id,
                    observation_date,
                    observation.get("value"),
                    observation.get("realtime_start"),
                    observation.get("realtime_end"),
                    json.dumps(observation.get("raw_observation", observation)),
                ),
            )
            persisted_count += 1

    conn.commit()
    cur.close()
    conn.close()

    return persisted_count


def persist_macro_snapshot(macro_snapshot: dict):
    if not macro_snapshot:
        return

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO macro_snapshots (
            snapshot_date,
            fed_funds_rate,
            cpi_value,
            cpi_yoy,
            cpi_3m_annualized,
            unemployment_rate,
            unemployment_trend,
            treasury_10y,
            treasury_2y,
            yield_curve_spread,
            yield_curve_state,
            interest_rate_trend,
            inflation_trend,
            macro_regime,
            macro_risk_score,
            summary,
            raw_macro
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (snapshot_date)
        DO UPDATE SET
            fed_funds_rate = EXCLUDED.fed_funds_rate,
            cpi_value = EXCLUDED.cpi_value,
            cpi_yoy = EXCLUDED.cpi_yoy,
            cpi_3m_annualized = EXCLUDED.cpi_3m_annualized,
            unemployment_rate = EXCLUDED.unemployment_rate,
            unemployment_trend = EXCLUDED.unemployment_trend,
            treasury_10y = EXCLUDED.treasury_10y,
            treasury_2y = EXCLUDED.treasury_2y,
            yield_curve_spread = EXCLUDED.yield_curve_spread,
            yield_curve_state = EXCLUDED.yield_curve_state,
            interest_rate_trend = EXCLUDED.interest_rate_trend,
            inflation_trend = EXCLUDED.inflation_trend,
            macro_regime = EXCLUDED.macro_regime,
            macro_risk_score = EXCLUDED.macro_risk_score,
            summary = EXCLUDED.summary,
            raw_macro = EXCLUDED.raw_macro;
        """,
        (
            date.today(),
            macro_snapshot.get("fed_funds_rate"),
            macro_snapshot.get("cpi_value"),
            macro_snapshot.get("cpi_yoy"),
            macro_snapshot.get("cpi_3m_annualized"),
            macro_snapshot.get("unemployment_rate"),
            macro_snapshot.get("unemployment_trend"),
            macro_snapshot.get("treasury_10y"),
            macro_snapshot.get("treasury_2y"),
            macro_snapshot.get("yield_curve_spread"),
            macro_snapshot.get("yield_curve_state"),
            macro_snapshot.get("interest_rate_trend"),
            macro_snapshot.get("inflation_trend"),
            macro_snapshot.get("macro_regime"),
            macro_snapshot.get("macro_risk_score"),
            macro_snapshot.get("summary"),
            json.dumps(macro_snapshot),
        ),
    )

    conn.commit()
    cur.close()
    conn.close()
