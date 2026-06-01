from datetime import datetime
import sys
import time

from app.renderers.report import generate_report
from app.renderers.web_export import export_web_report
from app.ai.gemini_client import analyze_market
from app.ai.news_analyzer import analyze_news_events
from app.renderers.telegram import send_telegram_message
from app.collectors.macro import collect_macro_context
from app.collectors.breadth import collect_sector_breadth
from app.collectors.earnings import collect_earnings_context
from app.collectors.fmp_quotes import collect_fmp_quotes
from app.collectors.fmp_profile import collect_company_profile
from app.collectors.fmp_fundamentals import collect_fundamentals
from app.collectors.fred_macro import collect_fred_macro
from app.collectors.news_intelligence import collect_news_intelligence
from app.analytics.macro_regime_engine import build_macro_snapshot
from app.analytics.investor_ranking import build_investor_rankings
from app.config.symbols import CORE_SYMBOLS, FMP_WATCHLIST, FUNDAMENTAL_SYMBOLS
from app.processors.confidence_engine import unify_confidence
from app.db.repositories import save_market_snapshot
from app.db.intelligence_persistence import (
    persist_intelligence_report,
    persist_event_snapshot,
    persist_fundamental_snapshot,
    persist_fred_observations,
    persist_investor_scores,
    persist_macro_snapshot,
    persist_technical_snapshot,
)
from app.logger import setup_logger

log = setup_logger()

VALID_MODES = {"full", "degraded", "offline"}

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

def parse_mode() -> str:
    if len(sys.argv) < 2:
        return "full"

    mode = sys.argv[1].strip().lower()

    if mode not in VALID_MODES:
        raise ValueError(f"Invalid mode '{mode}'. Use: full, degraded, offline")

    return mode


def extract_headlines(news_events) -> list:
    headlines = []

    if isinstance(news_events, list):
        for item in news_events:
            if isinstance(item, dict):
                title = item.get("title") or item.get("headline") or item.get("summary")
                if title:
                    headlines.append(str(title))

    elif isinstance(news_events, dict):
        for value in news_events.values():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        title = item.get("title") or item.get("headline") or item.get("summary")
                        if title:
                            headlines.append(str(title))

    return headlines


def build_offline_market_ai() -> dict:
    return {
        "market_regime": "MIXED",
        "confidence": 50,
        "quick_take": (
            "Offline mode active. AI market analysis is unavailable, so AlphaScope "
            "is using a deterministic fallback."
        ),
        "macro_summary": [
            "Macro and technical data collected where available.",
            "AI interpretation disabled in offline mode.",
        ],
        "strong_sectors": ["Unavailable in offline fallback"],
        "weak_sectors": ["Unavailable in offline fallback"],
        "watchlist_names": ["Unavailable in offline fallback"],
        "event_risk_names": ["Unavailable in offline fallback"],
        "overheated_names": [],
        "weak_names": [],
        "short_term_outlook": "Neutral until AI analysis or expanded deterministic scoring is available.",
        "medium_term_outlook": "Monitor trend, volatility, breadth, and macro conditions.",
        "major_risks": [
            "AI provider unavailable",
            "Reduced signal quality in offline mode",
        ],
        "recommended_posture": "Defensive-neutral posture until full intelligence is restored.",
        "bullish_signals": [],
        "bearish_signals": [],
        "risk_flags": ["Offline fallback mode", "AI market interpretation unavailable"],
        "executive_summary": "Offline fallback intelligence generated.",
    }


def build_offline_news_ai(news_events=None) -> dict:
    headlines = extract_headlines(news_events) if news_events else []

    return {
        "market_regime_bias": "MIXED",
        "event_regime": "MIXED",
        "confidence": 50,
        "event_confidence": 50,
        "executive_summary": (
            "Offline mode active. Event AI synthesis is unavailable; raw headlines "
            "are retained where available."
        ),
        "macro_risks": ["Event classification unavailable in offline mode"],
        "macro_opportunities": [],
        "sector_watchlist": [],
        "key_catalysts": headlines[:10],
        "major_headlines": headlines[:10],
        "bullish_events": [],
        "bearish_events": [],
        "neutral_events": headlines[:10],
        "risk_events": ["AI event interpretation unavailable"],
        "headlines": headlines,
    }


def build_offline_unified(ai: dict, news_ai: dict) -> dict:
    return {
        "final_regime": "MIXED",
        "final_confidence": 50,
        "combined_score": 0,
        "systemic_event": False,
        "market_regime": ai.get("market_regime", "MIXED"),
        "market_confidence": ai.get("confidence", 50),
        "event_confidence": news_ai.get("event_confidence", news_ai.get("confidence", 50)),
        "event_raw_confidence": news_ai.get("confidence", 50),
        "market_weight": 0.50,
        "event_weight": 0.50,
        "diagnostics": [
            "Offline deterministic fallback active",
            "Gemini calls bypassed",
            "FMP disabled in offline mode",
        ],
    }


def format_unified_confidence(unified: dict) -> str:
    diagnostics = "\n".join([f"- {item}" for item in unified.get("diagnostics", [])])

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


def build_telegram_summary(
    mode: str,
    unified: dict,
    ai: dict,
    news_ai: dict,
    macro_context: dict,
    investor_rankings: list | None = None,
) -> str:
    macro_lines = []

    if isinstance(macro_context, dict):
        for symbol, data in macro_context.items():
            if isinstance(data, dict):
                change = (
                    data.get("change_pct")
                    or data.get("changePercent")
                    or data.get("change_percentage")
                )

                if change is not None:
                    try:
                        macro_lines.append(f"{symbol}: {float(change):+.2f}%")
                    except (TypeError, ValueError):
                        pass

    macro_snapshot = "\n".join(macro_lines[:6]) or "Macro snapshot unavailable."

    strong_names = ", ".join(ai.get("watchlist_names", [])[:4]) or "N/A"
    overheated = ", ".join(ai.get("overheated_names", [])[:3]) or "None"
    weak_names = ", ".join(ai.get("weak_names", [])[:3]) or "None"

    event_regime = news_ai.get("event_regime") or news_ai.get("market_regime_bias") or "MIXED"
    event_conf = news_ai.get("event_confidence") or news_ai.get("confidence") or 50

    quick_take = ai.get("quick_take", "No summary available.")
    if len(quick_take) > 450:
        quick_take = quick_take[:450] + "..."

    posture = ai.get("recommended_posture") or "Cautious positioning advised."
    if len(posture) > 250:
        posture = posture[:250] + "..."

    opportunity_lines = []
    for item in (investor_rankings or [])[:5]:
        symbol = item.get("symbol", "N/A")
        company = item.get("company") or symbol
        score = item.get("buy_score")
        recommendation = item.get("recommendation", "N/A")
        dividend = item.get("dividend_yield")

        if len(company) > 28:
            company = company[:25] + "..."

        try:
            score_text = f"{float(score):.1f}"
        except (TypeError, ValueError):
            score_text = "N/A"

        try:
            dividend_text = f"{float(dividend) * 100:.2f}%"
        except (TypeError, ValueError):
            dividend_text = "N/A"

        opportunity_lines.append(
            f"{symbol} ({company}) | Score {score_text} | {recommendation} | Div {dividend_text}"
        )

    top_opportunities = "\n".join(opportunity_lines) or "Top opportunities unavailable."

    return f"""AlphaScope Daily Brief
Mode: {mode.upper()}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}

FINAL REGIME
{unified['final_regime']} ({unified['final_confidence']}%)

QUICK TAKE
{quick_take}

MARKET SNAPSHOT
{macro_snapshot}

EVENT RISK
{event_regime} ({event_conf}%)

TECHNICAL SIGNALS
Strong: {strong_names}
Overheated: {overheated}
Weak: {weak_names}

POSTURE
{posture}

TOP OPPORTUNITIES
{top_opportunities}
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
- """ + ("\n- ".join(ai["overheated_names"]) if ai["overheated_names"] else "None") + f"""

Weak Names:
- """ + ("\n- ".join(ai["weak_names"]) if ai["weak_names"] else "None") + f"""

Short-Term Outlook:
{ai["short_term_outlook"]}

Medium-Term Outlook:
{ai["medium_term_outlook"]}

Major Risks:
- """ + "\n- ".join(ai["major_risks"])


def format_news_intelligence(news: dict) -> str:
    macro_opps = "\n- ".join(news["macro_opportunities"]) if news["macro_opportunities"] else "None"
    sector_watchlist = "\n- ".join(news["sector_watchlist"]) if news["sector_watchlist"] else "None"
    key_catalysts = "\n- ".join(news["key_catalysts"]) if news["key_catalysts"] else "None"

    return f"""Market Regime Bias: {news['market_regime_bias']}
Raw AI Confidence: {news['confidence']}%

Executive Summary:
{news['executive_summary']}

Macro Risks:
- """ + "\n- ".join(news["macro_risks"]) + f"""

Macro Opportunities:
- {macro_opps}

Sector Watchlist:
- {sector_watchlist}

Key Catalysts:
- {key_catalysts}"""


def format_earnings_context(data: dict) -> str:
    lines = []

    for symbol, details in data.items():
        if details.get("status") != "OK":
            continue

        lines.append(f"{symbol} — {details['earnings_date']} ({details['event_risk']})")

    return "\n".join(lines) if lines else "No earnings context available."


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
        if profile.get("status") == "OK":
            lines.append(
                f"{symbol}: "
                f"{profile.get('company_name')} | "
                f"Sector: {profile.get('sector')} | "
                f"Industry: {profile.get('industry')} | "
                f"Beta: {profile.get('beta')} | "
                f"Market Cap: {profile.get('market_cap')}"
            )

    return "\n".join(lines) if lines else "No company profile context available."


def format_fundamentals(data: dict) -> str:
    if not data:
        return "No fundamentals available."

    lines = []

    for symbol, f in data.items():
        if f.get("status") == "OK":
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

    return "\n".join(lines) if lines else "Fundamentals unavailable."


def collect_fmp_layer(mode: str):
    if mode in {"degraded", "offline"}:
        log.info("FMP layer disabled by selected mode")
        return (
            {},
            "FMP disabled by selected AlphaScope mode.",
            "Company profile intelligence disabled by selected AlphaScope mode.",
            "Fundamental intelligence disabled by selected AlphaScope mode.",
            {},
            {},
        )

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

    return (
        fmp_quotes,
        fmp_snapshot,
        company_profile_summary,
        fundamentals_summary,
        fundamentals,
        company_profiles,
    )


def persist_fundamental_results(fundamentals: dict):
    if not fundamentals:
        log.info("No fundamentals available to persist")
        return

    persisted_count = 0

    for symbol, snapshot in fundamentals.items():
        if not symbol or not snapshot:
            continue

        persist_fundamental_snapshot(symbol, snapshot)
        persisted_count += 1

    log.info(f"Persisted {persisted_count} fundamental snapshots")


def persist_investor_results(investor_rankings: list):
    if not investor_rankings:
        log.info("No investor rankings available to persist")
        return

    try:
        persist_investor_scores(investor_rankings)
        log.info(f"Persisted {len(investor_rankings)} investor score snapshots")
    except Exception as e:
        log.warning(f"Investor score persistence skipped: {e}")


def persist_technical_results(technical_results: list):
    if not technical_results:
        log.info("No technical results available to persist")
        return

    for stock in technical_results:
        symbol = stock.get("ticker")
        snapshot = stock.get("technical_snapshot")

        if not symbol or not snapshot:
            continue

        persist_technical_snapshot(symbol, snapshot)

    log.info(f"Persisted {len(technical_results)} technical snapshots")


def collect_fred_context() -> tuple[dict, dict]:
    try:
        fred_payload = collect_fred_macro()
        macro_snapshot = build_macro_snapshot(fred_payload)
        if fred_payload.get("status") != "OK":
            log.warning(f"FRED macro collection incomplete: {fred_payload.get('errors', {})}")
        return fred_payload, macro_snapshot
    except Exception as e:
        log.warning(f"FRED macro collection skipped: {e}")
        return (
            {
                "status": "ERROR",
                "source": "FRED",
                "series": {},
                "errors": {
                    "collector": str(e),
                },
                "cache_stats": {
                    "hits": 0,
                    "misses": 0,
                },
            },
            {
                "source": "FRED",
                "status": "ERROR",
                "macro_regime": "UNKNOWN",
                "inflation_trend": "UNKNOWN",
                "interest_rate_trend": "UNKNOWN",
                "yield_curve_state": "UNKNOWN",
                "unemployment_trend": "UNKNOWN",
                "macro_risk_score": 35,
                "summary": "FRED macro context unavailable.",
            },
        )


def persist_fred_results(fred_payload: dict, macro_snapshot: dict):
    try:
        observation_count = persist_fred_observations(fred_payload)
        if observation_count:
            log.info(f"Persisted {observation_count} FRED observations")

        if macro_snapshot:
            persist_macro_snapshot(macro_snapshot)
            log.info("Persisted FRED macro snapshot")
    except Exception as e:
        log.warning(f"FRED macro persistence skipped: {e}")


def build_full_report(mode: str):
    log.info(f"AlphaScope operating mode: {mode.upper()}")

    log.info("Generating technical report")
    technical_payload = generate_report()
    technical_report = technical_payload["report"]
    technical_results = technical_payload["technical_results"]

    log.info("Collecting macro context")
    macro_context = collect_macro_context(MACRO_SYMBOLS)

    log.info("Collecting FRED macro context")
    fred_payload, macro_snapshot = collect_fred_context()

    log.info("Collecting sector breadth")
    sector_breadth = collect_sector_breadth(SECTOR_SYMBOLS)

    log.info("Collecting earnings context")
    earnings_context = collect_earnings_context(CORE_SYMBOLS)

    (
        fmp_quotes,
        fmp_snapshot,
        company_profile_summary,
        fundamentals_summary,
        fundamentals,
        company_profiles,
    ) = collect_fmp_layer(mode)

    log.info("Collecting event intelligence")
    news_events = collect_news_intelligence()

    if mode == "offline":
        log.info("Offline mode active: bypassing Gemini event synthesis")
        news_ai = build_offline_news_ai(news_events)
    else:
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

    if mode == "offline":
        log.info("Offline mode active: bypassing Gemini market analysis")
        ai = build_offline_market_ai()
        unified = build_offline_unified(ai, news_ai)
    else:
        log.info("Running Gemini market analysis")
        ai = analyze_market(
            enhanced_context,
            macro_context,
            sector_breadth,
            earnings_context,
        )

        log.info("Running confidence arbitration")
        unified = unify_confidence(ai, news_ai)

    log.info("Persisting market snapshot")
    if fmp_quotes and fmp_quotes.get("status") == "OK":
        save_market_snapshot(fmp_quotes, unified)
    else:
        log.info("Skipping market snapshot persistence because FMP quotes are unavailable")

    log.info("Persisting technical snapshots")
    persist_technical_results(technical_results)

    log.info("Persisting fundamental snapshots")
    persist_fundamental_results(fundamentals)

    log.info("Generating investor rankings")
    investor_rankings = build_investor_rankings(
        fundamentals=fundamentals,
        company_profiles=company_profiles,
        fmp_quotes=fmp_quotes,
    )

    log.info("Persisting investor rankings")
    persist_investor_results(investor_rankings)

    log.info("Persisting AI intelligence report")
    persist_intelligence_report(ai)

    log.info("Persisting event intelligence snapshot")
    persist_event_snapshot(news_ai)

    log.info("Persisting FRED macro context")
    persist_fred_results(fred_payload, macro_snapshot)

    ai_summary = format_ai_summary(ai)
    news_summary = format_news_intelligence(news_ai)
    unified_summary = format_unified_confidence(unified)
    earnings_summary = format_earnings_context(earnings_context)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    full_report = f"""AlphaScope Daily Market Intelligence
Generated: {timestamp}
Mode: {mode.upper()}

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

    return {
        "report": full_report,
        "ai": ai,
        "news_ai": news_ai,
        "unified": unified,
        "macro_context": macro_context,
        "fred_payload": fred_payload,
        "macro_snapshot": macro_snapshot,
        "fmp_quotes": fmp_quotes,
        "fundamentals": fundamentals,
        "company_profiles": company_profiles,
        "investor_rankings": investor_rankings,
    }


def save_report(report_text: str, mode: str):
    filename = f"reports/alphascope_{mode}_{datetime.now().strftime('%Y%m%d')}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_text)

    log.info(f"Report saved to {filename}")

    return filename


def main():
    start = time.time()
    mode = parse_mode()

    log.info("AlphaScope run started")
    log.info(f"Requested mode: {mode.upper()}")

    try:
        result = build_full_report(mode)

        report = result["report"]
        ai = result["ai"]
        news_ai = result["news_ai"]
        unified = result["unified"]
        macro_context = result["macro_context"]
        macro_snapshot = result["macro_snapshot"]
        fmp_quotes = result["fmp_quotes"]
        fundamentals = result["fundamentals"]
        company_profiles = result["company_profiles"]
        investor_rankings = result["investor_rankings"]

        filename = save_report(report, mode)

        export_web_report(
            ai,
            unified,
            fmp_quotes,
            filename,
            company_profiles=company_profiles,
            fundamentals=fundamentals,
            investor_rankings=investor_rankings,
            macro_snapshot=macro_snapshot,
        )

        telegram_report = build_telegram_summary(
            mode,
            unified,
            ai,
            news_ai,
            macro_context,
            investor_rankings,
        )

        log.info("Sending Telegram executive summary")
        send_telegram_message(telegram_report)

        duration = round(time.time() - start, 2)
        log.info(f"AlphaScope completed successfully in {duration}s")

        print(report)
        print(f"\nSaved to {filename}")
        print("Web dashboard JSON exported.")
        print("Telegram executive summary delivered.")

    except Exception as e:
        log.exception(f"AlphaScope failed: {e}")
        raise


if __name__ == "__main__":
    main()
