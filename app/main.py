from datetime import datetime
import time

from app.renderers.report import generate_report
from app.ai.gemini_client import analyze_market
from app.renderers.telegram import send_telegram_message
from app.config import get_symbols
from app.collectors.macro import collect_macro_context
from app.collectors.breadth import collect_sector_breadth
from app.collectors.earnings import collect_earnings_context
from app.logger import setup_logger

log = setup_logger()


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

Event Risks:
- """ + "\n- ".join(ai["event_risk_names"]) + f"""

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


def format_earnings_context(data: dict) -> str:
    lines = []

    for symbol, details in data.items():
        if details["status"] != "OK":
            continue

        lines.append(
            f"{symbol} — {details['earnings_date']} ({details['event_risk']})"
        )

    return "\n".join(lines)


def build_full_report():
    log.info("Generating technical report")
    technical_report = generate_report()

    log.info("Collecting macro context")
    macro_context = collect_macro_context(
        get_symbols("macro")
    )

    log.info("Collecting sector breadth")
    sector_breadth = collect_sector_breadth(
        get_symbols("sectors")
    )

    log.info("Collecting earnings context")
    earnings_context = collect_earnings_context(
        get_symbols("core")
    )

    log.info("Running Gemini market analysis")
    ai = analyze_market(
        technical_report,
        macro_context,
        sector_breadth,
        earnings_context
    )

    ai_summary = format_ai_summary(ai)
    earnings_summary = format_earnings_context(earnings_context)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    full_report = f"""AlphaScope Daily Market Intelligence
Generated: {timestamp}

==============================

AI EXECUTIVE SUMMARY

{ai_summary}

==============================

EARNINGS EVENT CONTEXT

{earnings_summary}

==============================

TECHNICAL APPENDIX

{technical_report}
"""

    return full_report


def save_report(report_text):
    filename = f"reports/alphascope_{datetime.now().strftime('%Y%m%d')}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_text)

    log.info(f"Report saved to {filename}")

    return filename


def main():
    start = time.time()

    log.info("AlphaScope run started")

    try:
        report = build_full_report()
        filename = save_report(report)

        telegram_limit = 4000

        telegram_report = report.split(
            "==============================\n\nTECHNICAL APPENDIX"
        )[0]

        if len(telegram_report) > telegram_limit:
            chunks = [
                telegram_report[i:i + telegram_limit]
                for i in range(0, len(telegram_report), telegram_limit)
            ]

            log.info(
                f"Sending Telegram executive summary in {len(chunks)} chunks"
            )

            for chunk in chunks:
                send_telegram_message(chunk)

        else:
            log.info("Sending Telegram executive summary")
            send_telegram_message(telegram_report)

        duration = round(time.time() - start, 2)

        log.info(f"AlphaScope completed successfully in {duration}s")

        print(report)
        print(f"\nSaved to {filename}")
        print("Telegram delivery complete.")

    except Exception as e:
        log.exception(f"AlphaScope failed: {e}")
        raise


if __name__ == "__main__":
    main()