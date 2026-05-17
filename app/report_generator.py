from app.indicators import calculate_indicators
from app.screener import score_stock, classify
from datetime import datetime


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


def generate_report():
    results = []

    for ticker in WATCHLIST:
        metrics = calculate_indicators(ticker)
        scored = score_stock(metrics)

        if scored:
            scored["classification"] = classify(scored["score"])
            results.append(scored)

    results.sort(key=lambda x: x["score"], reverse=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    report = []
    report.append("# AlphaScope Daily Market Intelligence Report")
    report.append(f"Generated: {timestamp}")
    report.append("")

    for stock in results:
        metrics = stock["metrics"]

        report.append(
            f"## {stock['ticker']} — {stock['classification']} ({stock['score']}/100)"
        )

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

    with open(filename, "w") as f:
        f.write(report)

    print(report)
    print(f"\nSaved to {filename}")
