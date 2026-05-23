import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


def export_web_report(ai, unified, fmp_quotes, full_report_text=None):
    """
    Export AlphaScope intelligence for public dashboard + detailed intelligence page.
    """

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
            "AlphaScope intelligence currently unavailable."
        ),
        "bullish": ai.get(
            "watchlist_names",
            ["No active bullish opportunities"]
        )[:5],
        "bearish": ai.get(
            "weak_names",
            ["No immediate weakness detected"]
        )[:5],
        "ticker": ticker
    }

    latest_path = Path("web/data/latest-report.json")
    latest_path.parent.mkdir(parents=True, exist_ok=True)

    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(latest_output, f, indent=2)

    full_output = {
        "generated_at": toronto_time,
        "full_report": full_report_text or "No report available."
    }

    full_path = Path("web/data/full-report.json")

    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2)

    print("Web dashboard JSON exported.")