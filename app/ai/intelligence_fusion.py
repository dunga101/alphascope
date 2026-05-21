import os
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

from app.analytics.signal_engine import generate_signal, TechnicalSignal

load_dotenv()


@dataclass
class FundamentalSnapshot:
    symbol: str
    snapshot_date: str
    revenue: Optional[int]
    net_income: Optional[int]
    total_assets: Optional[int]
    total_liabilities: Optional[int]
    cash_and_equivalents: Optional[int]
    total_debt: Optional[int]
    operating_cash_flow: Optional[int]
    free_cash_flow: Optional[int]
    pe_ratio: Optional[float]
    eps: Optional[float]
    roe: Optional[float]
    debt_to_equity: Optional[float]


@dataclass
class MarketRegimeSnapshot:
    market_regime: str
    confidence_score: Optional[float]
    timestamp: Optional[str]


@dataclass
class IntelligenceFusion:
    symbol: str
    latest_date: str
    latest_close: float

    market_regime: str
    market_regime_confidence: Optional[float]

    technical_signal: str
    technical_confidence: int
    trend: str
    momentum: str
    volatility: str
    relative_strength: str
    risk_state: str

    fundamental_quality: str
    fundamental_score: int

    event_risk: str
    event_score: int

    composite_score: int
    recommendation: str
    executive_summary: str
    reasoning: List[str]


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def fetch_latest_fundamentals(symbol: str) -> Optional[FundamentalSnapshot]:
    query = """
        SELECT
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
            debt_to_equity
        FROM fundamental_snapshots
        WHERE symbol = %s
        ORDER BY snapshot_date DESC
        LIMIT 1;
    """

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (symbol.upper(),))
            row = cur.fetchone()

    if not row:
        return None

    return FundamentalSnapshot(
        symbol=row["symbol"],
        snapshot_date=str(row["snapshot_date"]),
        revenue=row["revenue"],
        net_income=row["net_income"],
        total_assets=row["total_assets"],
        total_liabilities=row["total_liabilities"],
        cash_and_equivalents=row["cash_and_equivalents"],
        total_debt=row["total_debt"],
        operating_cash_flow=row["operating_cash_flow"],
        free_cash_flow=row["free_cash_flow"],
        pe_ratio=float(row["pe_ratio"]) if row["pe_ratio"] is not None else None,
        eps=float(row["eps"]) if row["eps"] is not None else None,
        roe=float(row["roe"]) if row["roe"] is not None else None,
        debt_to_equity=float(row["debt_to_equity"]) if row["debt_to_equity"] is not None else None,
    )


def fetch_latest_market_regime() -> MarketRegimeSnapshot:
    query = """
        SELECT
            market_regime,
            confidence_score,
            timestamp
        FROM market_snapshots
        ORDER BY timestamp DESC
        LIMIT 1;
    """

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                row = cur.fetchone()

        if not row or not row.get("market_regime"):
            return MarketRegimeSnapshot("UNKNOWN", None, None)

        return MarketRegimeSnapshot(
            market_regime=str(row["market_regime"]).upper(),
            confidence_score=float(row["confidence_score"]) if row["confidence_score"] is not None else None,
            timestamp=str(row["timestamp"]) if row["timestamp"] is not None else None,
        )

    except Exception:
        return MarketRegimeSnapshot("UNKNOWN", None, None)


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def classify_fundamentals(
    fundamentals: Optional[FundamentalSnapshot],
) -> Tuple[str, int, List[str]]:
    reasons = []
    score = 0

    if fundamentals is None:
        return "UNKNOWN", 0, ["No fundamental snapshot found."]

    if fundamentals.net_income is not None:
        if fundamentals.net_income > 0:
            score += 7
            reasons.append("Company is profitable on a net income basis.")
        else:
            score -= 9
            reasons.append("Company has negative net income.")

    if fundamentals.operating_cash_flow is not None:
        if fundamentals.operating_cash_flow > 0:
            score += 6
            reasons.append("Operating cash flow is positive.")
        else:
            score -= 7
            reasons.append("Operating cash flow is negative.")

    if fundamentals.free_cash_flow is not None:
        if fundamentals.free_cash_flow > 0:
            score += 6
            reasons.append("Free cash flow is positive.")
        else:
            score -= 7
            reasons.append("Free cash flow is negative.")

    if fundamentals.eps is not None:
        if fundamentals.eps > 0:
            score += 4
            reasons.append("EPS is positive.")
        else:
            score -= 5
            reasons.append("EPS is negative.")

    if fundamentals.roe is not None:
        if fundamentals.roe >= 20:
            score += 6
            reasons.append("ROE is strong.")
        elif 10 <= fundamentals.roe < 20:
            score += 4
            reasons.append("ROE is healthy.")
        elif 0 < fundamentals.roe < 10:
            score += 1
            reasons.append("ROE is positive but modest.")
        else:
            score -= 5
            reasons.append("ROE is weak or negative.")

    if fundamentals.debt_to_equity is not None:
        if fundamentals.debt_to_equity < 0.5:
            score += 5
            reasons.append("Debt-to-equity is low.")
        elif 0.5 <= fundamentals.debt_to_equity <= 1.5:
            score += 2
            reasons.append("Debt-to-equity is manageable.")
        elif 1.5 < fundamentals.debt_to_equity <= 3:
            score -= 4
            reasons.append("Debt-to-equity is elevated.")
        else:
            score -= 7
            reasons.append("Debt-to-equity is high.")

    if fundamentals.cash_and_equivalents is not None and fundamentals.total_debt is not None:
        if fundamentals.cash_and_equivalents > fundamentals.total_debt:
            score += 5
            reasons.append("Cash and equivalents exceed total debt.")
        elif fundamentals.total_debt > 0:
            ratio = fundamentals.cash_and_equivalents / fundamentals.total_debt
            if ratio >= 0.5:
                score += 2
                reasons.append("Cash position covers a meaningful portion of debt.")
            else:
                score -= 3
                reasons.append("Cash position is limited relative to total debt.")

    if fundamentals.pe_ratio is not None:
        if 0 < fundamentals.pe_ratio <= 25:
            score += 3
            reasons.append("P/E ratio is within a reasonable valuation range.")
        elif 25 < fundamentals.pe_ratio <= 60:
            score -= 2
            reasons.append("P/E ratio is elevated.")
        elif fundamentals.pe_ratio > 60:
            score -= 5
            reasons.append("P/E ratio is very elevated.")
        else:
            reasons.append("P/E ratio is not meaningful or unavailable.")

    score = clamp(score, -20, 20)

    if score >= 15:
        quality = "HIGH"
    elif 5 <= score < 15:
        quality = "MEDIUM"
    elif -5 <= score < 5:
        quality = "LOW"
    else:
        quality = "WEAK"

    return quality, score, reasons


def classify_event_risk(symbol: str) -> Tuple[str, int, List[str]]:
    return "UNKNOWN", 0, ["Event risk not yet connected to persisted news intelligence."]


def score_market_regime(
    snapshot: MarketRegimeSnapshot,
    signal: TechnicalSignal,
) -> Tuple[int, List[str]]:
    regime = snapshot.market_regime
    confidence = snapshot.confidence_score
    reasons = []

    confidence_multiplier = 1.0
    if confidence is not None:
        confidence_multiplier = max(0.4, min(1.0, confidence / 100))

    if regime == "RISK_ON":
        base = 7
        reasons.append("Market regime is RISK_ON, supporting constructive setups.")
    elif regime == "RISK_OFF":
        if signal.volatility in ["ELEVATED", "HIGH"]:
            base = -12
            reasons.append("Market regime is RISK_OFF and the asset has elevated volatility.")
        else:
            base = -8
            reasons.append("Market regime is RISK_OFF, reducing risk appetite.")
    elif regime == "MIXED":
        base = -2
        reasons.append("Market regime is MIXED, requiring selective positioning.")
    else:
        base = 0
        reasons.append("Market regime is unknown.")

    adjusted = int(round(base * confidence_multiplier))
    return adjusted, reasons


def technical_score_from_confidence(signal: TechnicalSignal) -> int:
    raw = int(round((signal.confidence_score - 50) * 0.35))
    return clamp(raw, -20, 20)


def apply_technical_veto(
    composite_score: int,
    signal: TechnicalSignal,
    reasons: List[str],
) -> int:
    score = composite_score

    if signal.signal in ["MIXED_NEUTRAL"]:
        if score > 64:
            score = 64
            reasons.append("Technical veto applied: mixed-neutral technical signal caps composite score at 64.")

    if signal.signal in ["AVOID_WEAK_STRUCTURE", "DEFENSIVE_AVOID"]:
        if score > 45:
            score = 45
            reasons.append("Technical veto applied: weak technical structure caps composite score at 45.")

    if signal.trend in ["RECOVERING", "WEAK"] and score > 68:
        score = 68
        reasons.append("Technical veto applied: recovering or weak trend prevents aggressive scoring.")

    if signal.relative_strength in ["WEAK", "VERY_WEAK"] and score > 68:
        score = 68
        reasons.append("Technical veto applied: weak relative strength prevents aggressive scoring.")

    if signal.volatility == "HIGH" and score > 70:
        score = 70
        reasons.append("Risk veto applied: high volatility caps composite score at 70.")

    if signal.volatility == "ELEVATED" and signal.relative_strength in ["WEAK", "VERY_WEAK"] and score > 62:
        score = 62
        reasons.append("Risk veto applied: elevated volatility plus weak relative strength caps score at 62.")

    return score


def determine_recommendation(
    composite_score: int,
    signal: TechnicalSignal,
    fundamental_quality: str,
    event_risk: str,
    market_regime: str,
) -> str:
    if event_risk == "HIGH":
        return "WAIT_EVENT_RISK_HIGH"

    if market_regime == "RISK_OFF" and signal.volatility in ["ELEVATED", "HIGH"]:
        return "MONITOR_ONLY_RISK_OFF"

    if signal.signal in ["AVOID_WEAK_STRUCTURE", "DEFENSIVE_AVOID"]:
        return "AVOID_WEAK_STRUCTURE"

    if signal.signal == "MIXED_NEUTRAL":
        if composite_score >= 55:
            return "WATCHLIST_MIXED"
        return "CAUTION"

    if signal.trend in ["RECOVERING", "WEAK"]:
        if composite_score >= 60:
            return "WATCHLIST_RECOVERY"
        return "CAUTION"

    if signal.relative_strength in ["WEAK", "VERY_WEAK"]:
        if composite_score >= 55:
            return "WATCHLIST_WEAK_RS"
        return "CAUTION"

    if composite_score >= 82:
        if signal.momentum in ["OVERBOUGHT", "EXTREME_OVERBOUGHT"]:
            return "ACCUMULATE_ON_PULLBACK"
        if signal.volatility in ["ELEVATED", "HIGH"]:
            return "WATCHLIST_HIGH_QUALITY_VOLATILE"
        return "STRONG_BUY_CANDIDATE"

    if 68 <= composite_score < 82:
        if signal.volatility in ["ELEVATED", "HIGH"]:
            return "WATCHLIST_HIGH_BETA_LEADER"
        return "ACCUMULATE_SELECTIVELY"

    if 50 <= composite_score < 68:
        return "WATCHLIST"

    if 35 <= composite_score < 50:
        return "CAUTION"

    return "AVOID"


def build_executive_summary(
    symbol: str,
    signal: TechnicalSignal,
    fundamental_quality: str,
    market_regime: str,
    composite_score: int,
    recommendation: str,
) -> str:
    return (
        f"{symbol.upper()} shows a {signal.trend.lower()} technical structure with "
        f"{signal.momentum.lower()} momentum, {signal.volatility.lower()} volatility, "
        f"and {signal.relative_strength.lower()} relative strength versus SPY. "
        f"Fundamental quality is classified as {fundamental_quality.lower()}, while the broader "
        f"market regime is {market_regime}. Composite score is {composite_score}/100, producing "
        f"the recommendation: {recommendation}."
    )


def generate_fusion(symbol: str) -> Optional[IntelligenceFusion]:
    symbol = symbol.upper()

    signal = generate_signal(symbol)
    if signal is None:
        print(f"No technical signal available for {symbol}")
        return None

    fundamentals = fetch_latest_fundamentals(symbol)
    fundamental_quality, fundamental_score, fundamental_reasons = classify_fundamentals(fundamentals)

    event_risk, event_score, event_reasons = classify_event_risk(symbol)

    market_snapshot = fetch_latest_market_regime()
    market_score, market_reasons = score_market_regime(market_snapshot, signal)

    technical_score = technical_score_from_confidence(signal)

    reasons = []
    reasons.extend(signal.reasoning)
    reasons.extend(fundamental_reasons)
    reasons.extend(event_reasons)
    reasons.extend(market_reasons)

    raw_score = 50 + technical_score + fundamental_score + event_score + market_score
    composite_score = clamp(raw_score, 0, 88)
    composite_score = apply_technical_veto(composite_score, signal, reasons)

    recommendation = determine_recommendation(
        composite_score=composite_score,
        signal=signal,
        fundamental_quality=fundamental_quality,
        event_risk=event_risk,
        market_regime=market_snapshot.market_regime,
    )

    executive_summary = build_executive_summary(
        symbol=symbol,
        signal=signal,
        fundamental_quality=fundamental_quality,
        market_regime=market_snapshot.market_regime,
        composite_score=composite_score,
        recommendation=recommendation,
    )

    return IntelligenceFusion(
        symbol=symbol,
        latest_date=signal.latest_date,
        latest_close=signal.latest_close,
        market_regime=market_snapshot.market_regime,
        market_regime_confidence=market_snapshot.confidence_score,
        technical_signal=signal.signal,
        technical_confidence=signal.confidence_score,
        trend=signal.trend,
        momentum=signal.momentum,
        volatility=signal.volatility,
        relative_strength=signal.relative_strength,
        risk_state=signal.risk_state,
        fundamental_quality=fundamental_quality,
        fundamental_score=fundamental_score,
        event_risk=event_risk,
        event_score=event_score,
        composite_score=composite_score,
        recommendation=recommendation,
        executive_summary=executive_summary,
        reasoning=reasons,
    )


def fusion_to_dict(fusion: IntelligenceFusion) -> Dict[str, Any]:
    return asdict(fusion)


def print_fusion_report(symbol: str):
    fusion = generate_fusion(symbol)

    if fusion is None:
        print(f"No fusion report generated for {symbol.upper()}")
        return

    data = fusion_to_dict(fusion)

    print("\n" + "=" * 80)
    print(f"ALPHASCOPE INTELLIGENCE FUSION REPORT: {symbol.upper()}")
    print("=" * 80)

    for key, value in data.items():
        if key not in ["reasoning", "executive_summary"]:
            print(f"{key}: {value}")

    print("\nexecutive_summary:")
    print(data["executive_summary"])

    print("\nreasoning:")
    for reason in data["reasoning"]:
        print(f"- {reason}")


def main():
    test_symbols = ["SPY", "NVDA", "TSLA"]

    for symbol in test_symbols:
        print_fusion_report(symbol)


if __name__ == "__main__":
    main()