from datetime import datetime

from app.renderers.report import generate_report
from app.ai.gemini_client import analyze_market
from app.renderers.telegram import send_telegram_message
from app.config import get_symbols
from app.collectors.macro import collect_macro_context
from app.collectors.breadth import collect_sector_breadth


def format_ai_summary(ai: dict) -> str:
    return f"""Market Regime: {ai['market_regime']}
Confidence: {ai['confidence']}%

Macro Summary:
- """ + "\n- ".join(ai["macro_summary"]) + f"""

Strong Sectors:
- """ + "\n- ".join(ai["strong_sectors"]) + f"""

Weak Sectors:
- """ + "\n- ".join(ai["weak_sectors"]) + f"""

Top Candidates:
- """ + "\n- ".join(ai["top_candidates"]) + f"""

Overheated:
- """ + "\n- ".join(ai["overheated_names"]) + f"""

Weak Names:
- """ + "\n- ".join(ai["weak_names"]) + f"""

Short-Term Outlook:
{ai["short_term_outlook"]}

Medium-Term Outlook:
{ai["medium_term_outlook"]}

Major Risks:
- """ + "\n- ".join(ai["major_risks"])


def build_full_report():
    technical_report = generate_report()

    macro_context = collect_macro_context(
        get_symbols("macro")
    )

    sector_breadth = collect_sector_breadth(
        get_symbols("sectors")
    )

    ai = analyze_market(
        technical_report,
        macro_context,
        sector_breadth
    )

    ai_summary = format_ai_summary(ai)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    full_report = f"""AlphaScope Daily Market Intelligence
Generated: {timestamp}

==============================

AI EXECUTIVE SUMMARY

{ai_summary}

==============================

TECHNICAL APPENDIX

{technical_report}
"""

    return full_report


def save_report(report_text):
    filename = f"reports/alphascope_{datetime.now().strftime('%Y%m%d')}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_text)

    return filename


def main():
    report = build_full_report()
    filename = save_report(report)

    telegram_limit = 4000

    if len(report) > telegram_limit:
        chunks = [
            report[i:i + telegram_limit]
            for i in range(0, len(report), telegram_limit)
        ]

        for chunk in chunks:
            send_telegram_message(chunk)
    else:
        send_telegram_message(report)

    print(report)
    print(f"\nSaved to {filename}")
    print("Telegram delivery complete.")


if __name__ == "__main__":
    main()