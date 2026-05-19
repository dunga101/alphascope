from typing import Dict, Any
from app.processors.event_classifier import detect_systemic_event


REGIME_SCORES = {
    "STRONG RISK_ON": 2,
    "RISK_ON": 1,
    "NEUTRAL": 0,
    "MIXED": 0,
    "RISK_OFF": -1,
    "STRONG RISK_OFF": -2,
}


def _normalize_regime(regime: str) -> str:
    value = str(regime).upper().replace("-", "_").strip()

    if "STRONG" in value and "RISK_OFF" in value:
        return "STRONG RISK_OFF"

    if "STRONG" in value and "RISK_ON" in value:
        return "STRONG RISK_ON"

    if "RISK_OFF" in value:
        return "RISK_OFF"

    if "RISK_ON" in value:
        return "RISK_ON"

    if "MIXED" in value:
        return "MIXED"

    return "NEUTRAL"


def _regime_score(regime: str) -> int:
    return REGIME_SCORES.get(_normalize_regime(regime), 0)


def _same_direction(a: str, b: str) -> bool:
    return (_regime_score(a) * _regime_score(b)) > 0


def _is_strong(regime: str) -> bool:
    return abs(_regime_score(regime)) >= 2


def _confidence_gap_penalty(a: float, b: float) -> float:
    gap = abs(a - b)

    if gap >= 50:
        return 0.70

    if gap >= 35:
        return 0.80

    if gap >= 20:
        return 0.90

    return 1.0


def _systemic_event_confidence_cap(confidence: float) -> float:
    return min(confidence, 75)


def unify_confidence(
    market_ai: Dict[str, Any],
    event_ai: Dict[str, Any],
) -> Dict[str, Any]:

    market_regime = _normalize_regime(
        market_ai.get("market_regime", "NEUTRAL")
    )

    event_regime = _normalize_regime(
        event_ai.get("market_regime_bias", "NEUTRAL")
    )

    market_confidence = float(market_ai.get("confidence", 0))
    event_confidence = float(event_ai.get("confidence", 0))
    raw_event_confidence = event_confidence

    headlines = event_ai.get("headlines", [])
    systemic_event = detect_systemic_event(headlines)

    market_score = _regime_score(market_regime)
    event_score = _regime_score(event_regime)

    diagnostics = []

    market_weight = 0.65
    event_weight = 0.35

    diagnostics.append("Macro-first weighting applied")

    if systemic_event:
        diagnostics.append("Systemic event detected")

        event_confidence = _systemic_event_confidence_cap(event_confidence)

        diagnostics.append(
            f"Systemic event confidence capped at {round(event_confidence)}%"
        )

        market_weight = 0.45
        event_weight = 0.55

    else:
        if abs(event_score) <= 1 and event_confidence > 70:
            event_confidence = 70
            diagnostics.append("Non-systemic event confidence capped")

    aligned = _same_direction(market_regime, event_regime)

    if aligned:
        diagnostics.append("Signals aligned")

        if _is_strong(market_regime) and not systemic_event:
            market_weight = 0.75
            event_weight = 0.25
            diagnostics.append("Strong macro dominance")

    else:
        diagnostics.append("Signal conflict detected")

        if market_score != 0 and event_score != 0:
            market_confidence *= 0.85
            event_confidence *= 0.75
            diagnostics.append("Conflict penalty applied")

    combined_score = (
        market_score * (market_confidence / 100) * market_weight
        + event_score * (event_confidence / 100) * event_weight
    )

    weighted_confidence = (
        (market_confidence * market_weight)
        + (event_confidence * event_weight)
    )

    gap_penalty = _confidence_gap_penalty(
        market_confidence,
        event_confidence
    )

    if gap_penalty < 1.0:
        diagnostics.append(
            f"Confidence disagreement penalty applied ({gap_penalty})"
        )

    calibrated_confidence = weighted_confidence * gap_penalty

    if aligned:
        calibrated_confidence *= 1.05
        diagnostics.append("Alignment confirmation boost")

    final_confidence = min(100, round(calibrated_confidence))

    if combined_score <= -1.25:
        final_regime = "STRONG RISK_OFF"

    elif combined_score < -0.25:
        final_regime = "RISK_OFF"

    elif combined_score >= 1.25:
        final_regime = "STRONG RISK_ON"

    elif combined_score > 0.25:
        final_regime = "RISK_ON"

    else:
        final_regime = "MIXED"

    return {
        "final_regime": final_regime,
        "final_confidence": final_confidence,
        "combined_score": round(combined_score, 2),
        "market_regime": market_regime,
        "market_confidence": round(market_confidence),
        "event_regime": event_regime,
        "event_raw_confidence": round(raw_event_confidence),
        "event_confidence": round(event_confidence),
        "market_weight": market_weight,
        "event_weight": event_weight,
        "systemic_event": systemic_event,
        "diagnostics": diagnostics,
    }