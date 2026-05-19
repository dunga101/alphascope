from app.processors.indicators import calculate_indicators


def score_stock(metrics):
    if not metrics:
        return None

    score = 50
    reasons = []

    price = metrics["price"]
    sma20 = metrics["sma20"]
    sma50 = metrics["sma50"]
    rsi = metrics["rsi"]
    vr = metrics["volume_ratio"]

    # Trend structure
    if price > sma20:
        score += 10
        reasons.append("Above SMA20")
    else:
        score -= 10
        reasons.append("Below SMA20")

    if sma20 > sma50:
        score += 10
        reasons.append("Bullish trend (SMA20 > SMA50)")
    else:
        score -= 10
        reasons.append("Bearish trend (SMA20 < SMA50)")

    if price > sma50:
        score += 8
        reasons.append("Above SMA50")
    else:
        score -= 8
        reasons.append("Below SMA50")

    # Momentum
    if 55 <= rsi <= 68:
        score += 10
        reasons.append("Healthy momentum")

    elif 45 <= rsi < 55:
        score += 3
        reasons.append("Moderate momentum")

    elif 68 < rsi <= 75:
        score -= 5
        reasons.append("Strong but overheated")

    elif rsi < 35:
        score -= 10
        reasons.append("Weak momentum")

    else:
        reasons.append("Neutral momentum")

    # Participation
    if vr >= 2.0:
        score += 12
        reasons.append("Heavy participation")

    elif vr >= 1.5:
        score += 8
        reasons.append("Elevated participation")

    elif vr >= 1.0:
        score += 2
        reasons.append("Normal participation")

    else:
        score -= 10
        reasons.append("Low participation")

    score = max(0, min(100, round(score)))

    return {
        "ticker": metrics["ticker"],
        "score": score,
        "reasons": reasons,
        "metrics": metrics
    }


def classify(score):
    if score >= 75:
        return "HIGH CONVICTION"
    elif score >= 60:
        return "WATCHLIST"
    elif score >= 45:
        return "NEUTRAL"
    elif score >= 30:
        return "WEAK"
    return "AVOID"


if __name__ == "__main__":
    tickers = [
        "SPY",
        "QQQ",
        "NVDA",
        "MSFT",
        "SHOP.TO"
    ]

    results = []

    for ticker in tickers:
        metrics = calculate_indicators(ticker)
        scored = score_stock(metrics)

        if scored:
            scored["classification"] = classify(scored["score"])
            results.append(scored)

    results.sort(key=lambda x: x["score"], reverse=True)

    for stock in results:
        print(
            f"{stock['ticker']} | "
            f"{stock['score']} | "
            f"{stock['classification']}"
        )
        print(stock["reasons"])
        print("-" * 50)