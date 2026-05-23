import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


def export_web_report(ai, unified, fmp_quotes):
    """
    Export AlphaScope intelligence for public dashboard consumption.
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

    output = {
        "generated_at": toronto_time,

        "regime": unified.get(
            "final_regime",
            "UNKNOWN"
        ),

        "confidence": unified.get(
            "final_confidence",
            0
        ),

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

    out_path = Path("web/data/latest-report.json")
    out_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Web dashboard JSON exported -> {out_path}")