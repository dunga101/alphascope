import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


def export_web_report(ai, unified, fmp_quotes, report_file_path=None):
    ticker = []

    if fmp_quotes and fmp_quotes.get("status") == "OK":
        for symbol, quote in fmp_quotes.get("quotes", {}).items():
            ticker.append({
                "symbol": symbol,
                "price": f"${quote.get('price', 0)}",
                "change": f"{quote.get('changePercentage', 0):+.2f}%"
            })

    toronto_time = datetime.now(
        ZoneInfo("America/Toronto")
    ).strftime("%Y-%m-%d %H:%M %Z")

    latest_output = {
        "generated_at": toronto_time,
        "regime": unified.get("final_regime", "UNKNOWN"),
        "confidence": unified.get("final_confidence", 0),
        "summary": ai.get(
            "quick_take",
            "AlphaScope intelligence unavailable."
        ),
        "bullish": ai.get(
            "watchlist_names",
            []
        )[:5],
        "bearish": ai.get(
            "weak_names",
            []
        )[:5],
        "ticker": ticker
    }

    Path("web/data").mkdir(parents=True, exist_ok=True)

    with open("web/data/latest-report.json", "w", encoding="utf-8") as f:
        json.dump(latest_output, f, indent=2)

    full_report_text = "No report available."

    if report_file_path:
        report_path = Path(report_file_path)
        if report_path.exists():
            full_report_text = report_path.read_text(encoding="utf-8")

    full_output = {
        "generated_at": toronto_time,
        "full_report": full_report_text
    }

    with open("web/data/full-report.json", "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2)

    print("Web exports complete.")