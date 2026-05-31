from dataclasses import asdict, is_dataclass
from typing import Any, Optional


def _to_float(value) -> Optional[float]:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp(value: float, minimum: float = 0, maximum: float = 100) -> float:
    return max(minimum, min(maximum, value))


def _get_metric(source: Any, key: str):
    if source is None:
        return None

    if isinstance(source, dict):
        return source.get(key)

    return getattr(source, key, None)


def recommendation_for_score(buy_score: float) -> str:
    if buy_score >= 80:
        return "Strong Buy"
    if buy_score >= 65:
        return "Buy"
    if buy_score >= 50:
        return "Watch"
    return "Avoid"


def score_valuation(pe_ratio) -> float:
    pe = _to_float(pe_ratio)

    if pe is None or pe <= 0:
        return 45
    if pe <= 15:
        return 90
    if pe <= 25:
        return 75
    if pe <= 35:
        return 60
    if pe <= 50:
        return 45
    return 25


def score_dividend(dividend_yield) -> float:
    dividend = _to_float(dividend_yield)

    if dividend is None:
        return 40
    if dividend <= 0:
        return 35
    if dividend < 0.01:
        return 50
    if dividend < 0.025:
        return 70
    if dividend <= 0.06:
        return 90
    return 55


def score_financial_quality(roe, debt_to_equity, free_cash_flow) -> float:
    score = 50

    roe_value = _to_float(roe)
    if roe_value is not None:
        if roe_value >= 0.25:
            score += 25
        elif roe_value >= 0.15:
            score += 18
        elif roe_value >= 0.08:
            score += 8
        elif roe_value < 0:
            score -= 20

    debt_value = _to_float(debt_to_equity)
    if debt_value is not None:
        if debt_value <= 0.5:
            score += 15
        elif debt_value <= 1.5:
            score += 8
        elif debt_value <= 3:
            score -= 8
        else:
            score -= 20

    fcf_value = _to_float(free_cash_flow)
    if fcf_value is not None:
        if fcf_value > 0:
            score += 15
        elif fcf_value < 0:
            score -= 20

    return round(_clamp(score), 2)


def score_price_position(distance_from_52w_low) -> float:
    distance = _to_float(distance_from_52w_low)

    if distance is None:
        return 50
    if distance < 0:
        return 40
    if distance <= 10:
        return 85
    if distance <= 25:
        return 75
    if distance <= 50:
        return 60
    if distance <= 100:
        return 45
    return 30


def score_technical(rsi, technical_confidence=None) -> float:
    confidence = _to_float(technical_confidence)
    rsi_value = _to_float(rsi)

    if confidence is None:
        score = 50
    else:
        score = confidence

    if rsi_value is not None:
        if 45 <= rsi_value <= 65:
            score += 10
        elif 65 < rsi_value <= 75:
            score -= 5
        elif rsi_value > 75:
            score -= 15
        elif rsi_value < 35:
            score -= 10

    return round(_clamp(score), 2)


def score_investor_opportunity(
    symbol: str,
    fundamentals: Optional[dict],
    profile: Optional[dict] = None,
    quote: Optional[dict] = None,
    technical_indicators: Any = None,
    technical_signal: Any = None,
) -> dict:
    fundamentals = fundamentals or {}
    profile = profile or {}
    quote = quote or {}

    technical_data = (
        asdict(technical_indicators)
        if technical_indicators is not None and is_dataclass(technical_indicators)
        else technical_indicators or {}
    )

    pe_ratio = fundamentals.get("pe_ratio")
    roe = fundamentals.get("roe")
    debt_to_equity = fundamentals.get("debt_to_equity")
    dividend_yield = fundamentals.get("dividend_yield")
    free_cash_flow = fundamentals.get("free_cash_flow")

    distance_from_52w_low = _get_metric(
        technical_data,
        "distance_from_52w_low_pct",
    )

    if distance_from_52w_low is None:
        price = _to_float(quote.get("price"))
        year_low = _to_float(quote.get("yearLow"))
        if price is not None and year_low not in (None, 0):
            distance_from_52w_low = ((price - year_low) / year_low) * 100

    rsi = _get_metric(technical_data, "rsi14")
    technical_confidence = _get_metric(technical_signal, "confidence_score")

    valuation_score = score_valuation(pe_ratio)
    dividend_score = score_dividend(dividend_yield)
    financial_quality_score = score_financial_quality(
        roe,
        debt_to_equity,
        free_cash_flow,
    )
    price_position_score = score_price_position(distance_from_52w_low)
    technical_score = score_technical(rsi, technical_confidence)

    buy_score = round(
        (
            valuation_score * 0.25
            + dividend_score * 0.15
            + financial_quality_score * 0.30
            + price_position_score * 0.15
            + technical_score * 0.15
        ),
        2,
    )

    company_name = (
        profile.get("company_name")
        or quote.get("name")
        or symbol.upper()
    )

    result = {
        "symbol": symbol.upper(),
        "company": company_name,
        "sector": profile.get("sector"),
        "buy_score": buy_score,
        "recommendation": recommendation_for_score(buy_score),
        "valuation_score": round(valuation_score, 2),
        "dividend_score": round(dividend_score, 2),
        "financial_quality_score": round(financial_quality_score, 2),
        "price_position_score": round(price_position_score, 2),
        "technical_score": round(technical_score, 2),
        "dividend_yield": dividend_yield,
        "pe_ratio": pe_ratio,
        "distance_from_52w_low": (
            round(distance_from_52w_low, 2)
            if distance_from_52w_low is not None
            else None
        ),
        "rsi": rsi,
    }

    result["raw_score"] = {
        "fundamentals_available": bool(fundamentals),
        "technical_available": bool(technical_data),
        "weights": {
            "valuation": 0.25,
            "dividend": 0.15,
            "financial_quality": 0.30,
            "price_position": 0.15,
            "technical": 0.15,
        },
    }

    return result
