from datetime import datetime
import time

from app.renderers.report import generate_report
from app.ai.gemini_client import analyze_market
from app.renderers.telegram import send_telegram_message
from app.config import get_symbols
from app.collectors.macro import collect_macro_context
from app.collectors.breadth import collect_sector_breadth
from app.collectors.earnings import collect_earnings_context
from app.collectors.fmp_quotes import collect_fmp_quotes
from app.collectors.fmp_profile import collect_company_profile
from app.collectors.fmp_fundamentals import collect_fundamentals
from app.logger import setup_logger

log = setup_logger()

FMP_WATCHLIST = [
    "SPY",
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "META",
    "GOOGL",
]

SKIP_FUNDAMENTALS = {"SPY", "QQQ"}


def format_ai_summary(ai: dict) -> str:
    return f"""Market Regime: {ai['market_regime']}
Confidence: {ai['confidence']}%

Macro Summary:
- """ + "\n- ".join(ai["macro_summary"]) + f"""

Strong Sectors:
- """ + "\n- ".join(ai["strong_sectors"]) + f"""

Weak Sectors:
- """ + "\n- ".join(ai["weak_sectors"]) + f"""

Watchlist Names:
- """ + "\n- ".join(ai["watchlist_names"]) + f"""

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


def format_fmp_snapshot(data: dict) -> str:
    if data.get("status") != "OK":
        return f"FMP quote snapshot unavailable: {data.get('error', 'Unknown error')}"

    lines = []

    for symbol, quote in data["quotes"].items():
        lines.append(
            f"{symbol}: "
            f"${quote['price']} | "
            f"{quote['changePercentage']:.2f}% | "
            f"Vol {int(quote['volume']):,}"
        )

    if data.get("errors"):
        lines.append("")
        lines.append("FMP ERRORS:")

        for symbol, err in data["errors"].items():
            lines.append(f"{symbol}: {err}")

    return "\n".join(lines)


def format_company_profiles(profiles: dict) -> str:
    if not profiles:
        return "No company profile context available."

    lines = []

    for symbol, profile in profiles.items():
        if profile.get("status") != "OK":
            continue

        lines.append(
            f"{symbol}: "
            f"{profile.get('company_name')} | "
            f"Sector: {profile.get('sector')} | "
            f"Industry: {profile.get('industry')} | "
            f"Beta: {profile.get('beta')} | "
            f"Market Cap: {profile.get('market_cap')}"
        )

    return "\n".join(lines)


def format_fundamentals(data: dict) -> str:
    if not data:
        return "No fundamentals available."

    lines = []

    for symbol, f in data.items():
        if f.get("status") != "OK":
            continue

        lines.append(
            f"{symbol}: "
            f"Revenue={f.get('revenue')} | "
            f"NetIncome={f.get('net_income')} | "
            f"FCF={f.get('free_cash_flow')} | "
            f"Debt={f.get('total_debt')} | "
            f"CurrentRatio={f.get('current_ratio')} | "
            f"GrossMargin={f.get('gross_margin')} | "
            f"OperatingMargin={f.get('operating_margin')} | "
            f"NetMargin={f.get('net_margin')}"
        )

    return "\n".join(lines)


def build_full_report():
    log.info("Generating technical report")
    technical_report = generate_report()

    log.info("Collecting macro context")
    macro_context = collect_macro_context(get_symbols("macro"))

    log.info("Collecting sector breadth")
    sector_breadth = collect_sector_breadth(get_symbols("sectors"))

    log.info("Collecting earnings context")
    earnings_context = collect_earnings_context(get_symbols("core"))

    log.info(f"Collecting FMP quote snapshot ({len(FMP_WATCHLIST)} symbols)")
    fmp_quotes = collect_fmp_quotes(FMP_WATCHLIST)

    cache_stats = fmp_quotes.get("cache_stats", {})
    log.info(
        f"FMP cache stats: "
        f"HIT={cache_stats.get('hits', 0)} "
        f"MISS={cache_stats.get('misses', 0)}"
    )

    fmp_snapshot = format_fmp_snapshot(fmp_quotes)

    log.info("Collecting company profile intelligence")
    company_profiles = {}

    for symbol in FMP_WATCHLIST:
        profile = collect_company_profile(symbol)

        if profile.get("status") == "OK":
            company_profiles[symbol] = profile
        else:
            log.warning(
                f"Profile lookup failed for {symbol}: "
                f"{profile.get('reason', 'Unknown error')}"
            )

    company_profile_summary = format_company_profiles(company_profiles)

    log.info("Collecting fundamentals intelligence")
    fundamentals = {}

    for symbol in FMP_WATCHLIST:
        if symbol in SKIP_FUNDAMENTALS:
            continue

        f = collect_fundamentals(symbol)

        if f.get("status") == "OK":
            fundamentals[symbol] = f
        else:
            log.warning(
                f"Fundamentals lookup failed for {symbol}: "
                f"{f.get('reason', 'Unknown error')}"
            )

    fundamentals_summary = format_fundamentals(fundamentals)

    enhanced_context = f"""
LIVE MARKET SNAPSHOT

{fmp_snapshot}

COMPANY PROFILE INTELLIGENCE

{company_profile_summary}

FUNDAMENTALS INTELLIGENCE

{fundamentals_summary}

TECHNICAL ANALYSIS

{technical_report}
"""

    log.info("Running Gemini market analysis")
    ai = analyze_market(
        enhanced_context,
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

QUICK TAKE

{ai['quick_take']}

==============================

AI EXECUTIVE SUMMARY

{ai_summary}

==============================

LIVE MARKET SNAPSHOT

{fmp_snapshot}

==============================

COMPANY INTELLIGENCE

{company_profile_summary}

==============================

FUNDAMENTALS INTELLIGENCE

{fundamentals_summary}

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