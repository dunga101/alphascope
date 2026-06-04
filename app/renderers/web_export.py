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


def _coerce_json_list(value):
    if isinstance(value, list):
        return value

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []

    return []


def _metric_from_raw_signals(raw_signals, key):
    data = _coerce_json_object(raw_signals)
    metrics = data.get("metrics")

    if isinstance(metrics, dict) and key in metrics:
        return metrics.get(key)

    return data.get(key)


def _build_missing_data(row):
    missing = []

    required_fields = {
        "current_price": "Current price",
        "dividend_yield": "Dividend yield",
        "pe_ratio": "P/E ratio",
        "roe": "ROE",
        "sector": "Sector",
        "rsi": "RSI",
    }

    for key, label in required_fields.items():
        if row.get(key) is None:
            missing.append(f"{label} is unavailable.")

    missing_labels = {
        "pe_ratio": "P/E ratio",
        "roe": "ROE",
        "dividend_yield": "Dividend yield",
        "debt_to_equity": "Debt to equity",
        "free_cash_flow": "Free cash flow",
    }

    for field in row.get("missing_fundamental_fields") or []:
        label = missing_labels.get(field, field.replace("_", " ").title())
        message = f"{label} is unavailable."
        if message not in missing:
            missing.append(message)

    return missing


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
    raw_score = _coerce_json_object(row.get("raw_score"))
    metric_sources = raw_score.get("metric_sources") or {}
    data_status = (
        row.get("data_status")
        or raw_score.get("data_status")
        or "UNKNOWN"
    )
    providers_available = (
        _coerce_json_list(row.get("providers_available"))
        or raw_score.get("providers_available")
        or []
    )
    missing_fundamental_fields = (
        _coerce_json_list(row.get("missing_fields"))
        or raw_score.get("missing_fundamental_fields")
        or []
    )

    ranking = {
        "rank": int(row.get("rank")) if row.get("rank") is not None else None,
        "symbol": row.get("symbol"),
        "company": row.get("company_name") or row.get("symbol"),
        "current_price": _json_number(row.get("current_price") or raw_score.get("current_price")),
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
        "data_status": data_status,
        "data_quality_label": (
            row.get("data_quality_label")
            or raw_score.get("data_quality_label")
            or data_status.replace("_", " ").title()
        ),
        "data_completeness_percent": _json_number(
            row.get("data_completeness_percent")
            if row.get("data_completeness_percent") is not None
            else raw_score.get("data_completeness_percent")
        ),
        "provider_used": row.get("provider_used") or raw_score.get("provider_used"),
        "providers_available": providers_available,
        "pe_ratio_source": row.get("pe_ratio_source") or metric_sources.get("pe_ratio"),
        "roe_source": row.get("roe_source") or metric_sources.get("roe"),
        "dividend_yield_source": (
            row.get("dividend_yield_source")
            or metric_sources.get("dividend_yield")
        ),
        "debt_to_equity_source": (
            row.get("debt_to_equity_source")
            or metric_sources.get("debt_to_equity")
        ),
        "free_cash_flow_source": (
            row.get("free_cash_flow_source")
            or metric_sources.get("free_cash_flow")
        ),
        "missing_fundamental_fields": missing_fundamental_fields,
    }

    ranking["strengths"] = _build_strengths(ranking)
    ranking["risks"] = _build_risks(ranking)
    ranking["missing_data"] = _build_missing_data(ranking)
    ranking["score_breakdown"] = {
        "valuation": ranking["valuation_score"],
        "dividend": ranking["dividend_score"],
        "financial_quality": ranking["financial_quality_score"],
        "price_position": ranking["price_position_score"],
        "technical": ranking["technical_score"],
    }

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


def _compact_opportunity(row):
    return {
        "rank": row.get("rank"),
        "symbol": row.get("symbol"),
        "company": row.get("company"),
        "sector": row.get("sector"),
        "current_price": row.get("current_price"),
        "dividend_yield": row.get("dividend_yield"),
        "buy_score": row.get("buy_score"),
        "recommendation": row.get("recommendation"),
        "data_status": row.get("data_status"),
        "data_quality_label": row.get("data_quality_label"),
        "data_completeness_percent": row.get("data_completeness_percent"),
    }


def _has_any(source, keys):
    return any(source.get(key) is not None for key in keys)


def _health_status(row):
    if row.get("data_status") == "INSUFFICIENT_DATA":
        return "INSUFFICIENT_DATA"

    checks = [
        row["quote_available"],
        row["profile_available"],
        row["ratios_available"],
        row["income_statement_available"],
        row["balance_sheet_available"],
        row["cash_flow_available"],
        row["technical_snapshot_available"],
        row["fundamental_snapshot_available"],
        row["investor_score_available"],
    ]

    if all(checks):
        return "COMPLETE"
    if any(checks):
        return "PARTIAL"
    return "MISSING"


def _build_data_health_row(
    symbol,
    quote_map,
    company_profiles,
    fundamentals,
    investor_rankings,
    generated_at_iso,
):
    symbol = symbol.upper()
    quote = quote_map.get(symbol) or {}
    profile = company_profiles.get(symbol) or {}
    fundamental = fundamentals.get(symbol) or {}
    ranking = investor_rankings.get(symbol) or {}
    raw_score = _coerce_json_object(ranking.get("raw_score"))
    data_status = (
        ranking.get("data_status")
        or raw_score.get("data_status")
        or (
            "COMPLETE"
            if fundamental.get("data_completeness_percent") == 100
            else "PARTIAL"
            if fundamental
            else "MISSING"
        )
    )
    missing_fields = (
        fundamental.get("missing_fields")
        or ranking.get("missing_fundamental_fields")
        or raw_score.get("missing_fundamental_fields")
        or []
    )
    available_fields = fundamental.get("available_fields") or []

    row = {
        "symbol": symbol,
        "quote_available": bool(quote),
        "profile_available": bool(profile),
        "ratios_available": _has_any(
            fundamental,
            ("pe_ratio", "dividend_yield", "debt_to_equity", "current_ratio"),
        ),
        "income_statement_available": _has_any(
            fundamental,
            ("revenue", "net_income", "eps"),
        ),
        "balance_sheet_available": _has_any(
            fundamental,
            ("total_assets", "total_liabilities", "cash_and_equivalents", "total_debt"),
        ),
        "cash_flow_available": _has_any(
            fundamental,
            ("operating_cash_flow", "free_cash_flow", "capital_expenditure"),
        ),
        "technical_snapshot_available": bool(raw_score.get("technical_available")),
        "fundamental_snapshot_available": bool(fundamental),
        "investor_score_available": bool(ranking),
        "data_status": data_status,
        "data_quality_label": data_status.replace("_", " ").title(),
        "data_completeness_percent": fundamental.get("data_completeness_percent"),
        "provider_used": fundamental.get("provider_used") or ranking.get("provider_used"),
        "providers_available": fundamental.get("providers_available") or ranking.get("providers_available") or [],
        "available_fields": available_fields,
        "missing_fields": missing_fields,
        "pe_ratio_source": fundamental.get("pe_ratio_source") or ranking.get("pe_ratio_source"),
        "roe_source": fundamental.get("roe_source") or ranking.get("roe_source"),
        "dividend_yield_source": (
            fundamental.get("dividend_yield_source")
            or ranking.get("dividend_yield_source")
        ),
        "last_update_timestamp": generated_at_iso,
        "status": "MISSING",
    }

    row["status"] = _health_status(row)

    return row


def _summarize_data_health(rows):
    total = len(rows)
    complete = sum(1 for row in rows if row["status"] == "COMPLETE")
    partial = sum(1 for row in rows if row["status"] == "PARTIAL")
    insufficient = sum(1 for row in rows if row["status"] == "INSUFFICIENT_DATA")
    missing = sum(1 for row in rows if row["status"] == "MISSING")
    quotes = sum(1 for row in rows if row["quote_available"])
    fundamentals = sum(1 for row in rows if row["fundamental_snapshot_available"])
    scores = sum(1 for row in rows if row["investor_score_available"])
    coverage = round((complete / total) * 100, 2) if total else 0
    provider_coverage = {
        "FMP": sum(1 for row in rows if "FMP" in (row.get("providers_available") or [])),
        "YAHOO": sum(1 for row in rows if "YAHOO" in (row.get("providers_available") or [])),
        "COMBINED": sum(1 for row in rows if row.get("provider_used") == "COMBINED"),
        "combined_symbols": sum(1 for row in rows if row.get("fundamental_snapshot_available")),
        "total_symbols": total,
    }
    metric_coverage = {}

    for field in ("pe_ratio", "roe", "dividend_yield"):
        source_key = f"{field}_source"
        missing_field_name = field
        available_rows = [
            row for row in rows
            if missing_field_name not in (row.get("missing_fields") or [])
            and row.get("fundamental_snapshot_available")
        ]
        metric_coverage[field] = {
            "available": len(available_rows),
            "fmp": sum(1 for row in available_rows if row.get(source_key) == "FMP"),
            "yahoo": sum(1 for row in available_rows if row.get(source_key) == "YAHOO"),
            "unknown": sum(1 for row in available_rows if not row.get(source_key) or row.get(source_key) == "UNKNOWN"),
            "missing": total - len(available_rows),
        }

    warnings = []
    if fundamentals < total:
        warnings.append(f"Fundamentals coverage below symbol count: {fundamentals}/{total}.")
    if scores < total:
        warnings.append(f"Investor score coverage below symbol count: {scores}/{total}.")
    if coverage < 95:
        warnings.append(f"Complete coverage below 95%: {coverage}%.")

    return {
        "total_symbols": total,
        "complete_symbols": complete,
        "partial_symbols": partial,
        "insufficient_data_symbols": insufficient,
        "missing_symbols": missing,
        "coverage_percentage": coverage,
        "quotes_available": quotes,
        "fundamentals_available": fundamentals,
        "scores_available": scores,
        "provider_coverage": provider_coverage,
        "metric_coverage": metric_coverage,
        "missing_symbols_list": [
            row["symbol"] for row in rows
            if row["status"] in {"MISSING", "INSUFFICIENT_DATA"}
        ],
        "warnings": warnings,
    }


def export_data_health(
    generated_at,
    generated_at_iso,
    fmp_quotes=None,
    company_profiles=None,
    fundamentals=None,
    investor_rankings=None,
    symbols=None,
):
    if symbols is None:
        from app.analytics.investor_ranking import get_investor_symbols

        symbols = get_investor_symbols()

    quote_map = {}
    if fmp_quotes and fmp_quotes.get("status") == "OK":
        quote_map = fmp_quotes.get("quotes", {}) or {}

    company_profiles = company_profiles or {}
    fundamentals = fundamentals or {}
    investor_rankings = {
        item.get("symbol", "").upper(): item
        for item in (investor_rankings or [])
        if item.get("symbol")
    }
    symbols = [symbol.upper() for symbol in symbols]

    rows = [
        _build_data_health_row(
            symbol,
            quote_map,
            company_profiles,
            fundamentals,
            investor_rankings,
            generated_at_iso,
        )
        for symbol in symbols
    ]
    summary = _summarize_data_health(rows)

    output = {
        "generated_at": generated_at,
        "generated_at_iso": generated_at_iso,
        "generation_status": "success",
        "summary": summary,
        "symbols": rows,
    }

    Path("web/data").mkdir(parents=True, exist_ok=True)

    with open("web/data/data-health.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=_json_default)

    return output


def export_web_report(
    ai,
    unified,
    fmp_quotes,
    report_file_path=None,
    company_profiles=None,
    fundamentals=None,
    investor_rankings=None,
    macro_snapshot=None,
    data_health_symbols=None,
):
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
        "ticker": ticker,
        "macro": macro_snapshot or {
            "status": "UNAVAILABLE",
            "macro_regime": "UNKNOWN",
            "inflation_trend": "UNKNOWN",
            "interest_rate_trend": "UNKNOWN",
            "yield_curve_state": "UNKNOWN",
            "summary": "FRED macro context unavailable.",
        },
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
    data_health_output = export_data_health(
        generated_at,
        generated_at_iso,
        fmp_quotes=fmp_quotes,
        company_profiles=company_profiles,
        fundamentals=fundamentals,
        investor_rankings=investor_rankings,
        symbols=data_health_symbols,
    )

    latest_output["top_opportunities"] = [
        _compact_opportunity(row)
        for row in investor_output.get("rankings", [])[:5]
    ]
    latest_output["data_quality"] = data_health_output["summary"]

    with open("web/data/latest-report.json", "w", encoding="utf-8") as f:
        json.dump(latest_output, f, indent=2)

    if investor_output["generation_status"] == "error":
        print("Investor rankings export completed with errors.")

    print("Web exports complete.")
