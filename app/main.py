from datetime import datetime
import time

from app.renderers.report import generate_report
from app.ai.gemini_client import analyze_market
from app.ai.news_analyzer import analyze_news_events
from app.renderers.telegram import send_telegram_message
from app.collectors.macro import collect_macro_context
from app.collectors.breadth import collect_sector_breadth
from app.collectors.earnings import collect_earnings_context
from app.collectors.fmp_quotes import collect_fmp_quotes
from app.collectors.fmp_profile import collect_company_profile
from app.collectors.fmp_fundamentals import collect_fundamentals
from app.collectors.news_intelligence import collect_news_intelligence
from app.processors.confidence_engine import unify_confidence
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

FUNDAMENTAL_SYMBOLS = [
    "AAPL",
    "MSFT",
    "NVDA",
]

MACRO_SYMBOLS = [
    "^GSPC",
    "^IXIC",
    "^DJI",
    "^VIX",
    "^TNX",
    "GC=F",
    "CL=F",
    "BTC-USD",
]

SECTOR_SYMBOLS = [
    "XLF",
    "XLK",
    "XLE",
    "XLI",
    "XLV",
    "XLY",
    "XLP",
    "XLU",
    "XLRE",
    "XLC",
]

CORE_SYMBOLS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "META",
    "GOOGL",
    "TSLA",
]


def extract_headlines(news_events) -> list:
    headlines = []

    if isinstance(news_events, list):
        for item in news_events:
            if isinstance(item, dict):
                title = (
                    item.get("title")
                    or item.get("headline")
                    or item.get("summary")
                )

                if title:
                    headlines.append(str(title))

    elif isinstance(news_events, dict):
        for value in news_events.values():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        title = (
                            item.get("title")
                            or item.get("headline")
                            or item.get("summary")
                        )

                        if title:
                            headlines.append(str(title))

    return headlines


def format_unified_confidence(unified: dict) -> str:
    diagnostics = "\n".join(
        [f"- {item}" for item in unified.get("diagnostics", [])]
    )

    return f"""Final Regime: {unified['final_regime']}
Final Confidence: {unified['final_confidence']}%
Composite Score: {unified['combined_score']}
Systemic Event Detected: {unified.get('systemic_event', False)}

Inputs:
- Market AI: {unified['market_regime']} ({unified['market_confidence']}%)
- Event AI Raw/Governed: {unified.get('event_raw_confidence', unified['event_confidence'])}% → {unified['event_confidence']}%

Weights:
- Market Weight: {unified['market_weight']}
- Event Weight: {unified['event_weight']}

Fusion Diagnostics:
{diagnostics}
"""


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
- """ + (
        "\n- ".join(ai["overheated_names"])
        if ai["overheated_names"]
        else "None"
    ) + f"""

Weak Names:
- """ + (
        "\n- ".join(ai["weak_names"])
        if ai["weak_names"]
        else "None"
    ) + f"""

Short-Term Outlook:
{ai["short_term_outlook"]}

Medium-Term Outlook:
{ai["medium_term_outlook"]}

Major Risks:
- """ + "\n- ".join(ai["major_risks"])


def format_news_intelligence(news: dict) -> str:
    macro_opps = (
        "\n- ".join(news["macro_opportunities"])
        if news["macro_opportunities"]
        else "None"
    )

    return f"""Market Regime Bias: {news['market_regime_bias']}
Raw AI Confidence: {news['confidence']}%

Executive Summary:
{news['executive_summary']}

Macro Risks:
- """ + "\n- ".join(news["macro_risks"]) + f"""

Macro Opportunities:
- {macro_opps}

Sector Watchlist:
- """ + "\n- ".join(news["sector_watchlist"]) + f"""

Key Catalysts:
- """ + "\n- ".join(news["key_catalysts"])


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

    if not lines:
        return "Fundamentals unavailable (API quota exhausted or cache cold)."

    return "\n".join(lines)


def build_full_report():
    log.info("Generating technical report")
    technical_report = generate_report()

    log.info("Collecting macro context")
    macro_context = collect_macro_context(MACRO_SYMBOLS)

    log.info("Collecting sector breadth")
    sector_breadth = collect_sector_breadth(SECTOR_SYMBOLS)

    log.info("Collecting earnings context")
    earnings_context = collect_earnings_context(CORE_SYMBOLS)

    log.info("Collecting FMP quote snapshot")
    fmp_quotes = collect_fmp_quotes(FMP_WATCHLIST)
    fmp_snapshot = format_fmp_snapshot(fmp_quotes)

    log.info("Collecting company profiles")
    company_profiles = {}

    for symbol in FMP_WATCHLIST:
        profile = collect_company_profile(symbol)

        if profile.get("status") == "OK":
            company_profiles[symbol] = profile

    company_profile_summary = format_company_profiles(company_profiles)

    log.info("Collecting fundamentals")
    fundamentals = {}

    for symbol in FUNDAMENTAL_SYMBOLS:
        f = collect_fundamentals(symbol)

        if f.get("status") == "OK":
            fundamentals[symbol] = f

    fundamentals_summary = format_fundamentals(fundamentals)

    log.info("Collecting event intelligence")
    news_events = collect_news_intelligence()

    log.info("Running Gemini event synthesis")
    news_ai = analyze_news_events(news_events)
    news_ai["headlines"] = extract_headlines(news_events)

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

    log.info("Running confidence arbitration")
    unified = unify_confidence(ai, news_ai)

    ai_summary = format_ai_summary(ai)
    news_summary = format_news_intelligence(news_ai)
    unified_summary = format_unified_confidence(unified)
    earnings_summary = format_earnings_context(earnings_context)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    full_report = f"""AlphaScope Daily Market Intelligence
Generated: {timestamp}

==============================

UNIFIED MARKET REGIME

{unified_summary}

==============================

QUICK TAKE

{ai['quick_take']}

==============================

AI EVENT INTELLIGENCE

{news_summary}

==============================

AI MARKET INTELLIGENCE

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

        telegram_report = report.split(
            "==============================\n\nTECHNICAL APPENDIX"
        )[0]

        log.info("Sending Telegram report")
        send_telegram_message(telegram_report)

        duration = round(time.time() - start, 2)

        log.info(f"AlphaScope completed in {duration}s")

        print(report)
        print(f"\nSaved to {filename}")
        print("Telegram delivery complete.")

    except Exception as e:
        log.exception(f"AlphaScope failed: {e}")
        raise


if __name__ == "__main__":
    main()