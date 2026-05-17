from app.indicators import calculate_indicators


def score_stock(metrics):
    score = 0
    reasons = []

    if not metrics:
        return None

    # Trend (40 pts)
    if metrics["price"] > metrics["sma20"]:
        score += 20
        reasons.append("Above SMA20")
    else:
        reasons.append("Below SMA20")

    if metrics["sma20"] > metrics["sma50"]:
        score += 20
        reasons.append("Bullish trend (SMA20 > SMA50)")
    else:
        reasons.append("Bearish trend (SMA20 < SMA50)")

    # RSI (25 pts)
    rsi = metrics["rsi"]

    if 50 <= rsi <= 70:
        score += 25
        reasons.append("Healthy momentum")

    elif 40 <= rsi < 50:
        score += 15
        reasons.append("Moderate momentum")

    elif 70 < rsi <= 80:
        score += 10
        reasons.append("Strong but overheated")

    elif rsi < 30:
        score += 5
        reasons.append("Oversold / possible reversal")

    else:
        reasons.append("Weak momentum")

    # Volume participation (20 pts)
    vr = metrics["volume_ratio"]

    if vr >= 2.0:
        score += 20
        reasons.append("Heavy volume surge")

    elif vr >= 1.5:
        score += 15
        reasons.append("Elevated volume")

    elif vr >= 1.0:
        score += 8
        reasons.append("Normal participation")

    else:
        reasons.append("Low participation")

    # Stability bonus (15 pts)
    if metrics["price"] > metrics["sma50"]:
        score += 15
        reasons.append("Above SMA50")
    else:
        reasons.append("Below SMA50")

    return {
        "ticker": metrics["ticker"],
        "score": score,
        "reasons": reasons,
        "metrics": metrics
    }


def classify(score):
    if score >= 80:
        return "STRONG WATCH"
    elif score >= 65:
        return "WATCH"
    elif score >= 50:
        return "NEUTRAL"
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
