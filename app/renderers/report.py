from app.processors.indicators import calculate_indicators
from app.processors.screener import score_stock
from datetime import datetime
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
    "TSLA"
]


def apply_regime_penalty(score, regime):
    if regime == "STRONG RISK-OFF":
        return max(score - 25, 0)
    elif regime == "RISK-OFF":
        return max(score - 15, 0)
    elif regime == "RISK-ON":
        return min(score + 10, 100)
    elif regime == "STRONG RISK-ON":
        return min(score + 15, 100)

    return score


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
                market_regime["regime"]
            )

            scored["score"] = adjusted_score
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
        report.append(f"- Price: {metrics['price']}")
        report.append(f"- RSI: {metrics['rsi']}")
        report.append(f"- Volume Ratio: {metrics['volume_ratio']}")
        report.append(f"- SMA20: {metrics['sma20']}")
        report.append(f"- SMA50: {metrics['sma50']}")
        report.append(f"- Signals: {', '.join(stock['reasons'])}")
        report.append("")

    return "\n".join(report)


if __name__ == "__main__":
    report = generate_report()

    filename = "reports/daily_report.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)