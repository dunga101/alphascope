import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

from app.db.intelligence_persistence import fetch_latest_investor_rankings


def _json_default(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _to_float(value):
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _json_number(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value

    return _to_float(value)


def _coerce_json_object(value):
    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}

    return {}


def _metric_from_raw_signals(raw_signals, key):
    data = _coerce_json_object(raw_signals)
    metrics = data.get("metrics")

    if isinstance(metrics, dict) and key in metrics:
        return metrics.get(key)

    return data.get(key)


def _build_strengths(row):
    strengths = []

    if row.get("recommendation") in {"Strong Buy", "Buy"}:
        strengths.append(
            f"{row.get('recommendation')} recommendation based on composite investor score."
        )

    financial_quality = _to_float(row.get("financial_quality_score"))
    if financial_quality is not None and financial_quality >= 70:
        strengths.append("Financial quality score is above the preferred threshold.")

    valuation = _to_float(row.get("valuation_score"))
    if valuation is not None and valuation >= 70:
        strengths.append("Valuation score is supportive relative to the ranked universe.")

    dividend_yield = _to_float(row.get("dividend_yield"))
    if dividend_yield is not None and dividend_yield > 0:
        strengths.append("Dividend yield is present for income-oriented investors.")

    technical = _to_float(row.get("technical_score"))
    if technical is not None and technical >= 60:
        strengths.append("Technical score is constructive.")

    return strengths[:5]


def _build_risks(row):
    risks = []

    if row.get("recommendation") == "Avoid":
        risks.append("Composite investor score is below the investable threshold.")

    valuation = _to_float(row.get("valuation_score"))
    if valuation is not None and valuation < 50:
        risks.append("Valuation score is weak.")

    technical = _to_float(row.get("technical_score"))
    if technical is not None and technical < 50:
        risks.append("Technical score is weak.")

    if row.get("dividend_yield") is None:
        risks.append("Dividend yield is unavailable.")

    if row.get("roe") is None:
        risks.append("ROE is unavailable in the latest fundamentals snapshot.")

    return risks[:5]


def _format_investor_row(row):
    raw_signals = row.get("technical_raw_signals")

    ranking = {
        "rank": int(row.get("rank")) if row.get("rank") is not None else None,
        "symbol": row.get("symbol"),
        "company": row.get("company_name") or row.get("symbol"),
        "buy_score": _json_number(row.get("buy_score")),
        "recommendation": row.get("recommendation"),
        "dividend_yield": _json_number(row.get("dividend_yield")),
        "pe_ratio": _json_number(row.get("pe_ratio")),
        "roe": _json_number(row.get("roe")),
        "sector": row.get("sector"),
        "technical_score": _json_number(row.get("technical_score")),
        "valuation_score": _json_number(row.get("valuation_score")),
        "financial_quality_score": _json_number(row.get("financial_quality_score")),
        "dividend_score": _json_number(row.get("dividend_score")),
        "price_position_score": _json_number(row.get("price_position_score")),
        "debt_to_equity": _json_number(row.get("debt_to_equity")),
        "free_cash_flow": _json_number(row.get("free_cash_flow")),
        "rsi": _json_number(row.get("rsi") or _metric_from_raw_signals(raw_signals, "rsi")),
        "sma20": _json_number(_metric_from_raw_signals(raw_signals, "sma20")),
        "sma50": _json_number(_metric_from_raw_signals(raw_signals, "sma50")),
        "sma200": _json_number(_metric_from_raw_signals(raw_signals, "sma200")),
        "distance_from_52w_low": _json_number(row.get("distance_from_52w_low")),
    }

    ranking["strengths"] = _build_strengths(ranking)
    ranking["risks"] = _build_risks(ranking)

    return ranking


def export_investor_rankings(generated_at, generated_at_iso):
    status = "success"
    error = None

    try:
        rows = fetch_latest_investor_rankings()
        rankings = [_format_investor_row(row) for row in rows]
        if not rankings:
            status = "empty"
    except Exception as exc:
        rankings = []
        status = "error"
        error = str(exc) or repr(exc)

    output = {
        "generated_at": generated_at,
        "generated_at_iso": generated_at_iso,
        "generation_status": status,
        "count": len(rankings),
        "rankings": rankings,
    }

    if error:
        output["error"] = error

    Path("web/data").mkdir(parents=True, exist_ok=True)

    with open("web/data/investor-rankings.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=_json_default)

    return output


def export_web_report(ai, unified, fmp_quotes, report_file_path=None):
    ticker = []

    if fmp_quotes and fmp_quotes.get("status") == "OK":
        for symbol, quote in fmp_quotes.get("quotes", {}).items():
            ticker.append({
                "symbol": symbol,
                "price": f"${quote.get('price', 0)}",
                "change": f"{quote.get('changePercentage', 0):+.2f}%"
            })

    toronto_time = datetime.now(ZoneInfo("America/Toronto"))
    generated_at = toronto_time.strftime("%Y-%m-%d %H:%M %Z")
    generated_at_iso = toronto_time.isoformat()

    latest_output = {
        "generated_at": generated_at,
        "generated_at_iso": generated_at_iso,
        "generation_status": "success",
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
        "generated_at": generated_at,
        "generated_at_iso": generated_at_iso,
        "generation_status": "success",
        "full_report": full_report_text
    }

    with open("web/data/full-report.json", "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2)

    investor_output = export_investor_rankings(
        generated_at,
        generated_at_iso,
    )

    if investor_output["generation_status"] == "error":
        print("Investor rankings export completed with errors.")

    print("Web exports complete.")
