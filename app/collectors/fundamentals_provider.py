from app.collectors.fmp_fundamentals import collect_fundamentals
from app.collectors.yahoo_fundamentals import collect_yahoo_fundamentals

PROVIDER_FMP = "FMP"
PROVIDER_YAHOO = "YAHOO"
PROVIDER_UNKNOWN = "UNKNOWN"
PROVIDER_COMBINED = "COMBINED"

MERGE_FIELDS = (
    "pe_ratio",
    "forward_pe",
    "price_to_book",
    "earnings_yield",
    "dividend_yield",
    "gross_margin",
    "operating_margin",
    "net_margin",
    "profit_margin",
    "roe",
    "debt_to_equity",
    "current_ratio",
    "cash_and_equivalents",
    "total_debt",
    "market_cap",
    "sector",
    "industry",
    "beta",
    "revenue",
    "net_income",
    "operating_cash_flow",
    "free_cash_flow",
    "capital_expenditure",
    "eps",
)

COMPLETENESS_FIELDS = (
    "pe_ratio",
    "roe",
    "dividend_yield",
    "debt_to_equity",
    "free_cash_flow",
    "revenue",
    "total_debt",
    "operating_margin",
)

CRITICAL_FIELDS = (
    "pe_ratio",
    "roe",
    "dividend_yield",
)


def _to_float(value):
    if value is None or value == "":
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _valid_value(field: str, value) -> bool:
    if value is None or value == "":
        return False

    if field in {"sector", "industry"}:
        return isinstance(value, str) and bool(value.strip())

    number = _to_float(value)
    if number is None:
        return False

    if field in {"pe_ratio", "forward_pe", "price_to_book"}:
        return number > 0

    return True


def _provider_error(payload: dict | None):
    if not payload or payload.get("status") == "OK":
        return None

    return payload.get("reason") or payload.get("error") or "Provider unavailable."


def _status_ok(payload: dict | None) -> bool:
    return bool(payload and payload.get("status") == "OK")


def _source_for_field(payload: dict, provider: str, field: str) -> str:
    provider_fields = payload.get("provider_fields") or {}
    return provider_fields.get(field) or provider


def _calculate_completeness(result: dict) -> tuple[float, list[str], list[str]]:
    available = [
        field for field in COMPLETENESS_FIELDS
        if _valid_value(field, result.get(field))
    ]
    missing = [field for field in COMPLETENESS_FIELDS if field not in available]
    completeness = round((len(available) / len(COMPLETENESS_FIELDS)) * 100, 2)
    return completeness, available, missing


def merge_fundamental_payloads(
    symbol: str,
    fmp_payload: dict | None,
    yahoo_payload: dict | None,
) -> dict:
    symbol = symbol.strip().upper()
    fmp_ok = _status_ok(fmp_payload)
    yahoo_ok = _status_ok(yahoo_payload)
    fmp_payload = fmp_payload or {}
    yahoo_payload = yahoo_payload or {}

    result = {
        "status": "OK",
        "symbol": symbol,
        "source": PROVIDER_UNKNOWN,
        "provider_used": PROVIDER_UNKNOWN,
        "providers_available": [],
        "provider_errors": {},
        "raw_provider_data": {
            "fmp": fmp_payload.get("raw_provider_data", {}),
            "yahoo": yahoo_payload.get("raw_provider_data", {}),
        },
    }

    if fmp_ok:
        result["providers_available"].append(PROVIDER_FMP)
    else:
        error = _provider_error(fmp_payload)
        if error:
            result["provider_errors"][PROVIDER_FMP] = error

    if yahoo_ok:
        result["providers_available"].append(PROVIDER_YAHOO)
    else:
        error = _provider_error(yahoo_payload)
        if error:
            result["provider_errors"][PROVIDER_YAHOO] = error

    sources_used = set()

    for field in MERGE_FIELDS:
        selected_value = None
        selected_source = PROVIDER_UNKNOWN

        if fmp_ok and _valid_value(field, fmp_payload.get(field)):
            selected_value = fmp_payload.get(field)
            selected_source = _source_for_field(fmp_payload, PROVIDER_FMP, field)
        elif yahoo_ok and _valid_value(field, yahoo_payload.get(field)):
            selected_value = yahoo_payload.get(field)
            selected_source = _source_for_field(yahoo_payload, PROVIDER_YAHOO, field)

        result[field] = selected_value
        result[f"{field}_source"] = selected_source

        if selected_source != PROVIDER_UNKNOWN:
            sources_used.add(selected_source)

    if sources_used == {PROVIDER_FMP}:
        provider_used = PROVIDER_FMP
    elif sources_used == {PROVIDER_YAHOO}:
        provider_used = PROVIDER_YAHOO
    elif sources_used:
        provider_used = PROVIDER_COMBINED
    else:
        provider_used = PROVIDER_UNKNOWN

    result["source"] = provider_used
    result["provider_used"] = provider_used

    completeness, available_fields, missing_fields = _calculate_completeness(result)
    result["data_completeness_percent"] = completeness
    result["available_fields"] = available_fields
    result["missing_fields"] = missing_fields
    result["critical_missing_fields"] = [
        field for field in CRITICAL_FIELDS
        if not _valid_value(field, result.get(field))
    ]

    if not available_fields:
        result["status"] = "ERROR"
        result["reason"] = "No valid fundamentals from FMP or Yahoo."

    return result


def collect_combined_fundamentals(symbols: list[str]) -> tuple[dict, dict]:
    fundamentals = {}
    diagnostics = {
        "symbols": {},
        "provider_counts": {
            PROVIDER_FMP: 0,
            PROVIDER_YAHOO: 0,
            PROVIDER_COMBINED: 0,
            PROVIDER_UNKNOWN: 0,
        },
    }

    for symbol in symbols:
        symbol = symbol.upper()
        fmp_payload = collect_fundamentals(symbol)
        yahoo_payload = collect_yahoo_fundamentals(symbol)
        merged = merge_fundamental_payloads(symbol, fmp_payload, yahoo_payload)

        diagnostics["symbols"][symbol] = {
            "fmp_status": fmp_payload.get("status"),
            "yahoo_status": yahoo_payload.get("status"),
            "provider_used": merged.get("provider_used"),
            "data_completeness_percent": merged.get("data_completeness_percent"),
            "missing_fields": merged.get("missing_fields", []),
            "provider_errors": merged.get("provider_errors", {}),
        }
        diagnostics["provider_counts"][merged.get("provider_used", PROVIDER_UNKNOWN)] += 1

        if merged.get("status") == "OK":
            fundamentals[symbol] = merged

    return fundamentals, diagnostics
