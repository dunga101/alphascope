from datetime import datetime
from app.report_generator import generate_report
from app.ai_analyzer import analyze_market
from app.notifier import send_telegram_message


def build_full_report():
    technical_report = generate_report()
    ai_analysis = analyze_market(technical_report)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    full_report = f"""AlphaScope Daily Market Intelligence
Generated: {timestamp}

==============================

TECHNICAL SCREENING

{technical_report}

==============================

AI MARKET INTELLIGENCE

{ai_analysis}
"""

    return full_report


def save_report(report_text):
    filename = f"reports/alphascope_{datetime.now().strftime('%Y%m%d')}.md"

    with open(filename, "w") as f:
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
