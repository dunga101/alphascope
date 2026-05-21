from datetime import datetime

from app.processors.indicators import calculate_indicators
from app.processors.screener import score_stock, classify
from app.processors.signal_fusion import fuse_signals
from app.collectors.advanced_breadth import collect_advanced_breadth
from app.collectors.macro_signals import collect_macro_signals


WATCHLIST = [
    "SPY",
    "QQQ",
    "NVDA",
    "MSFT",
    "SHOP.TO",
    "AMD",
    "GOOGL",
    "AMZN",
    "META",
    "TSLA",
]


def apply_regime_penalty(score, regime):
    if regime == "STRONG RISK-OFF":
        return max(score - 25, 0)
    if regime == "RISK-OFF":
        return max(score - 15, 0)
    if regime == "RISK-ON":
        return min(score + 10, 100)
    if regime == "STRONG RISK-ON":
        return min(score + 15, 100)

    return score


def derive_technical_snapshot(stock: dict, market_regime: dict) -> dict:
    score = stock["score"]
    metrics = stock["metrics"]
    reasons = stock["reasons"]

    trend_score = 50
    if metrics["price"] > metrics["sma20"]:
        trend_score += 20
    else:
        trend_score -= 20

    if metrics["sma20"] > metrics["sma50"]:
        trend_score += 20
    else:
        trend_score -= 20

    momentum_score = 50
    rsi = metrics["rsi"]

    if 55 <= rsi <= 68:
        momentum_score = 80
    elif 45 <= rsi < 55:
        momentum_score = 60
    elif 68 < rsi <= 75:
        momentum_score = 55
    elif rsi < 35:
        momentum_score = 25

    volatility_score = 50
    risk_score = max(0, min(100, 100 - score))

    return {
        "signal_score": score,
        "trend_score": max(0, min(100, trend_score)),
        "momentum_score": momentum_score,
        "volatility_score": volatility_score,
        "risk_score": risk_score,
        "technical_regime": classify(score),
        "technical_confidence": score,
        "ticker": stock["ticker"],
        "metrics": metrics,
        "reasons": reasons,
        "market_regime": market_regime,
    }


def generate_report():
    results = []

    advanced_breadth = collect_advanced_breadth()
    macro_signals = collect_macro_signals()
    market_regime = fuse_signals(advanced_breadth, macro_signals)

    for ticker in WATCHLIST:
        metrics = calculate_indicators(ticker)
        scored = score_stock(metrics)

        if scored:
            adjusted_score = apply_regime_penalty(
                scored["score"],
                market_regime["regime"],
            )

            scored["score"] = adjusted_score
            scored["classification"] = classify(adjusted_score)
            scored["technical_snapshot"] = derive_technical_snapshot(
                scored,
                market_regime,
            )

            results.append(scored)

    results.sort(key=lambda x: x["score"], reverse=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    report = []
    report.append("# AlphaScope Daily Market Intelligence Report")
    report.append(f"Generated: {timestamp}")
    report.append("")

    report.append("## Market Regime")
    report.append("")
    report.append(f"**Regime:** {market_regime['regime']}")
    report.append(f"**Confidence:** {market_regime['confidence']}%")
    report.append(f"**Bias:** {market_regime['bias']}")
    report.append(f"**Composite Score:** {market_regime['score']}")
    report.append("")

    report.append("### Signal Breakdown")
    for note in market_regime["notes"]:
        report.append(f"- {note}")

    report.append("")
    report.append("## Technical Signal Matrix")
    report.append("")

    for stock in results:
        metrics = stock["metrics"]

        report.append(f"## {stock['ticker']}")
        report.append(f"- Raw Score: {stock['score']}/100")
        report.append(f"- Classification: {stock['classification']}")
        report.append(f"- Price: {metrics['price']}")
        report.append(f"- RSI: {metrics['rsi']}")
        report.append(f"- Volume Ratio: {metrics['volume_ratio']}")
        report.append(f"- SMA20: {metrics['sma20']}")
        report.append(f"- SMA50: {metrics['sma50']}")
        report.append(f"- Signals: {', '.join(stock['reasons'])}")
        report.append("")

    return {
        "report": "\n".join(report),
        "market_regime": market_regime,
        "technical_results": results,
    }


if __name__ == "__main__":
    result = generate_report()
    report = result["report"]

    filename = "reports/daily_report.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)