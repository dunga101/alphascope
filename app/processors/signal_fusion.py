def score_index_change(change: float) -> float:
    if change >= 2.0:
        return 1.0
    elif change >= 0.75:
        return 0.6
    elif change >= 0:
        return 0.2
    elif change >= -0.75:
        return -0.2
    elif change >= -2.0:
        return -0.6
    else:
        return -1.0


def score_vix(change: float) -> float:
    if change >= 8:
        return -1.0
    elif change >= 4:
        return -0.6
    elif change >= 0:
        return -0.2
    elif change >= -4:
        return 0.2
    else:
        return 0.6


def score_yield(change: float) -> float:
    if change >= 2:
        return -0.8
    elif change >= 0.5:
        return -0.4
    elif change >= -0.5:
        return 0
    elif change >= -2:
        return 0.3
    else:
        return 0.6


def fuse_signals(advanced_breadth: dict, macro_signals: dict) -> dict:
    total_score = 0
    notes = []

    breadth_weights = {
        "sp500": 25,
        "nasdaq_100": 25,
        "dow": 15,
        "small_caps": 15,
    }

    for name, weight in breadth_weights.items():
        item = advanced_breadth.get(name, {})
        change = item.get("change_pct")

        if change is None:
            continue

        normalized = score_index_change(change)
        contribution = normalized * weight
        total_score += contribution

        notes.append(
            f"{name}: {change:.2f}% (impact {contribution:+.1f})"
        )

    vix_change = macro_signals.get("vix", {}).get("change_pct")
    if vix_change is not None:
        contribution = score_vix(vix_change) * 12
        total_score += contribution
        notes.append(
            f"VIX: {vix_change:.2f}% (impact {contribution:+.1f})"
        )

    yield_change = macro_signals.get("ten_year_yield", {}).get("change_pct")
    if yield_change is not None:
        contribution = score_yield(yield_change) * 8
        total_score += contribution
        notes.append(
            f"10Y Yield: {yield_change:.2f}% (impact {contribution:+.1f})"
        )

    confidence = min(abs(total_score), 100)

    if total_score >= 50:
        regime = "STRONG RISK-ON"
        bias = "Broad bullish participation"
    elif total_score >= 20:
        regime = "RISK-ON"
        bias = "Constructive trend"
    elif total_score <= -50:
        regime = "STRONG RISK-OFF"
        bias = "Capital preservation / defensive posture"
    elif total_score <= -20:
        regime = "RISK-OFF"
        bias = "Caution / weak participation"
    else:
        regime = "NEUTRAL"
        bias = "Mixed market conditions"

    return {
        "regime": regime,
        "confidence": round(confidence, 1),
        "bias": bias,
        "score": round(total_score, 1),
        "notes": notes,
    }