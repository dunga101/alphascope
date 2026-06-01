from statistics import mean
from typing import Any


def _to_float(value: Any):
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _observations(series: dict) -> list[dict]:
    values = series.get("observations", []) if isinstance(series, dict) else []
    return [
        item
        for item in values
        if item.get("date") and _to_float(item.get("value")) is not None
    ]


def _latest_value(series: dict):
    latest = series.get("latest") if isinstance(series, dict) else None
    if isinstance(latest, dict):
        return _to_float(latest.get("value"))

    observations = _observations(series)
    if not observations:
        return None
    return _to_float(observations[-1].get("value"))


def _latest_date(series: dict):
    latest = series.get("latest") if isinstance(series, dict) else None
    if isinstance(latest, dict):
        return latest.get("date")

    observations = _observations(series)
    if not observations:
        return None
    return observations[-1].get("date")


def calculate_cpi_yoy(cpi_series: dict):
    observations = _observations(cpi_series)
    if len(observations) < 13:
        return None

    latest = _to_float(observations[-1].get("value"))
    prior = _to_float(observations[-13].get("value"))

    if latest is None or prior in (None, 0):
        return None

    return round(((latest / prior) - 1) * 100, 2)


def calculate_cpi_3m_annualized(cpi_series: dict):
    observations = _observations(cpi_series)
    if len(observations) < 4:
        return None

    latest = _to_float(observations[-1].get("value"))
    prior = _to_float(observations[-4].get("value"))

    if latest is None or prior in (None, 0):
        return None

    return round((((latest / prior) ** 4) - 1) * 100, 2)


def inflation_trend(cpi_series: dict) -> str:
    yoy = calculate_cpi_yoy(cpi_series)
    annualized_3m = calculate_cpi_3m_annualized(cpi_series)
    observations = _observations(cpi_series)

    if yoy is None or annualized_3m is None or len(observations) < 14:
        return "UNKNOWN"

    current = _to_float(observations[-1].get("value"))
    prior_month = _to_float(observations[-2].get("value"))
    prior_year = _to_float(observations[-13].get("value"))
    prior_year_prev_month = _to_float(observations[-14].get("value"))

    if None in (current, prior_month, prior_year, prior_year_prev_month):
        return "UNKNOWN"

    prior_yoy = ((prior_month / prior_year_prev_month) - 1) * 100

    if yoy < prior_yoy - 0.1 and annualized_3m <= yoy + 0.25:
        return "COOLING"
    if yoy > prior_yoy + 0.1 or annualized_3m > yoy + 0.75:
        return "REACCELERATING"
    return "STABLE"


def _average_recent(series: dict, window: int):
    observations = _observations(series)
    if len(observations) < window:
        return None

    values = [_to_float(item.get("value")) for item in observations[-window:]]
    values = [value for value in values if value is not None]

    if not values:
        return None
    return mean(values)


def interest_rate_trend(fed_funds_series: dict, dgs2_series: dict) -> str:
    latest_fed = _latest_value(fed_funds_series)
    latest_2y = _latest_value(dgs2_series)
    avg_fed = _average_recent(fed_funds_series, 3)
    avg_2y = _average_recent(dgs2_series, 30)

    deltas = []
    if latest_fed is not None and avg_fed is not None:
        deltas.append(latest_fed - avg_fed)
    if latest_2y is not None and avg_2y is not None:
        deltas.append(latest_2y - avg_2y)

    if not deltas:
        return "UNKNOWN"

    average_delta = mean(deltas)
    if average_delta >= 0.15:
        return "RISING"
    if average_delta <= -0.15:
        return "FALLING"
    return "STABLE"


def yield_curve_state(dgs10_series: dict, dgs2_series: dict) -> tuple[str, float | None]:
    ten_year = _latest_value(dgs10_series)
    two_year = _latest_value(dgs2_series)

    if ten_year is None or two_year is None:
        return "UNKNOWN", None

    spread = round(ten_year - two_year, 2)
    if spread < -0.25:
        return "INVERTED", spread
    if spread <= 0.25:
        return "FLAT", spread
    return "NORMAL", spread


def unemployment_trend(unrate_series: dict) -> str:
    observations = _observations(unrate_series)
    if len(observations) < 4:
        return "UNKNOWN"

    latest = _to_float(observations[-1].get("value"))
    prior = _to_float(observations[-4].get("value"))

    if latest is None or prior is None:
        return "UNKNOWN"

    delta = latest - prior
    if delta >= 0.3:
        return "RISING"
    if delta <= -0.3:
        return "FALLING"
    return "STABLE"


def macro_regime(
    inflation: str,
    rates: str,
    curve: str,
    labor: str,
) -> str:
    if "UNKNOWN" in {inflation, rates, curve, labor}:
        return "UNKNOWN"

    if curve == "INVERTED" and labor == "RISING":
        return "RECESSION_RISK"
    if inflation == "REACCELERATING" and labor == "RISING":
        return "STAGFLATION_RISK"
    if inflation == "REACCELERATING" and rates == "RISING":
        return "RESTRICTIVE_POLICY"
    if inflation == "COOLING" and labor in {"STABLE", "FALLING"} and curve == "NORMAL":
        return "GOLDILOCKS"
    if inflation == "COOLING" and rates == "FALLING":
        return "RECESSION_RISK" if labor == "RISING" else "DISINFLATIONARY_GROWTH"
    if rates == "RISING":
        return "RESTRICTIVE_POLICY"
    return "MIXED"


def macro_risk_score(regime: str, curve: str, inflation: str, labor: str) -> float:
    score = 35

    if regime in {"RECESSION_RISK", "STAGFLATION_RISK"}:
        score += 35
    elif regime == "RESTRICTIVE_POLICY":
        score += 25
    elif regime == "MIXED":
        score += 15
    elif regime == "GOLDILOCKS":
        score -= 15

    if curve == "INVERTED":
        score += 15
    if inflation == "REACCELERATING":
        score += 15
    if labor == "RISING":
        score += 15

    return round(max(0, min(100, score)), 2)


def build_macro_summary(snapshot: dict) -> str:
    regime = snapshot.get("macro_regime", "UNKNOWN")
    inflation = snapshot.get("inflation_trend", "UNKNOWN")
    rates = snapshot.get("interest_rate_trend", "UNKNOWN")
    curve = snapshot.get("yield_curve_state", "UNKNOWN")
    spread = snapshot.get("yield_curve_spread")

    spread_text = f"{spread:.2f}%" if spread is not None else "unavailable"

    return (
        f"Macro regime is {regime}. Inflation trend is {inflation}, "
        f"interest rate trend is {rates}, and the yield curve is {curve} "
        f"with a 10Y-2Y spread of {spread_text}."
    )


def build_macro_snapshot(fred_payload: dict) -> dict:
    series = fred_payload.get("series", {}) if isinstance(fred_payload, dict) else {}

    fed_funds = series.get("FEDFUNDS", {})
    cpi = series.get("CPIAUCSL", {})
    unemployment = series.get("UNRATE", {})
    dgs10 = series.get("DGS10", {})
    dgs2 = series.get("DGS2", {})

    inflation = inflation_trend(cpi)
    rates = interest_rate_trend(fed_funds, dgs2)
    curve, spread = yield_curve_state(dgs10, dgs2)
    labor = unemployment_trend(unemployment)
    regime = macro_regime(inflation, rates, curve, labor)

    snapshot = {
        "source": "FRED",
        "status": fred_payload.get("status", "ERROR") if isinstance(fred_payload, dict) else "ERROR",
        "fed_funds_rate": _latest_value(fed_funds),
        "fed_funds_date": _latest_date(fed_funds),
        "cpi_value": _latest_value(cpi),
        "cpi_date": _latest_date(cpi),
        "cpi_yoy": calculate_cpi_yoy(cpi),
        "cpi_3m_annualized": calculate_cpi_3m_annualized(cpi),
        "unemployment_rate": _latest_value(unemployment),
        "unemployment_date": _latest_date(unemployment),
        "unemployment_trend": labor,
        "treasury_10y": _latest_value(dgs10),
        "treasury_10y_date": _latest_date(dgs10),
        "treasury_2y": _latest_value(dgs2),
        "treasury_2y_date": _latest_date(dgs2),
        "yield_curve_spread": spread,
        "yield_curve_state": curve,
        "interest_rate_trend": rates,
        "inflation_trend": inflation,
        "macro_regime": regime,
        "macro_risk_score": macro_risk_score(regime, curve, inflation, labor),
        "errors": fred_payload.get("errors", {}) if isinstance(fred_payload, dict) else {},
    }
    snapshot["summary"] = build_macro_summary(snapshot)

    return snapshot
