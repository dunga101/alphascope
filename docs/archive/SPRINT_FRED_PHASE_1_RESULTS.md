# Sprint FRED Phase 1 Results

Generated: 2026-06-01

## Scope Implemented

Implemented Phase 1 through Phase 6 from `SPRINT_FRED_IMPLEMENTATION_PLAN.md`.

Not implemented, per approved scope:

- Dashboard UI changes
- Telegram changes
- FMP redesign
- Yahoo migration
- Additional APIs beyond FRED
- Gemini prompt changes
- 50-symbol expansion

## Schema Changes

Added `app/db/migrate_fred_macro.sql` and extended `app/db/schema_intelligence.sql`.

New tables:

- `fred_observations`
  - Stores normalized FRED series observations by `series_id` and `observation_date`.
  - Includes `value`, realtime metadata, source, timestamps, and raw JSON.
  - Unique key: `(series_id, observation_date)`.
- `macro_snapshots`
  - Stores one compact daily macro snapshot.
  - Includes Fed Funds, CPI, CPI YoY, CPI 3-month annualized, unemployment, 10Y, 2Y, yield curve spread/state, trend classifications, macro regime, risk score, summary, and raw JSON.
  - Unique key: `snapshot_date`.

New indexes:

- `idx_fred_observations_series_date`
- `idx_macro_snapshots_date`

Migration status:

- Migration applied successfully to PostgreSQL.
- Readback verification:
  - `fred_observations`: 264 rows
  - latest `macro_snapshots`: `2026-06-01`, `MIXED`, `REACCELERATING`, `STABLE`, `NORMAL`, risk score `65.0`

## Files Added

- `app/collectors/fred_macro.py`
- `app/analytics/macro_regime_engine.py`
- `app/collectors/test_fred_macro.py`
- `app/analytics/test_macro_regime_engine.py`
- `app/db/migrate_fred_macro.sql`
- `SPRINT_FRED_PHASE_1_RESULTS.md`

## Files Modified

- `app/main.py`
- `app/db/intelligence_persistence.py`
- `app/db/schema_intelligence.sql`
- `app/renderers/web_export.py`
- `app/renderers/test_web_export.py`

## Collector Behavior

FRED series collected:

- `FEDFUNDS`
- `CPIAUCSL`
- `UNRATE`
- `DGS10`
- `DGS2`

Configuration:

- Uses `FRED_API_KEY` from `.env`.
- Uses `data/cache/fred/` for per-series JSON cache files.
- Uses `FRED_CACHE_HOURS`, default `6`, for daily series.
- Uses `FRED_MONTHLY_CACHE_HOURS`, default `12`, for monthly series.

Failure behavior:

- Missing API key returns a structured FRED error payload.
- Per-series API failures are captured in `errors`.
- FRED collection failures do not fail the AlphaScope run.
- FRED persistence failures do not fail the AlphaScope run.
- FRED request error strings are sanitized so API keys are not exported.

## Analytics Added

Added `app/analytics/macro_regime_engine.py`.

Calculations:

- CPI YoY inflation
- CPI 3-month annualized inflation
- Inflation trend
- Fed Funds trend
- Yield curve spread
- Yield curve state
- Unemployment trend
- Macro regime classification
- Macro risk score
- Compact macro summary

## Pipeline Integration

Integrated into `python -m app.main full` without changing Gemini prompt inputs.

Execution path:

1. Existing market and technical collection runs.
2. Existing macro market context runs.
3. FRED macro context is collected.
4. Existing FMP, fundamentals, news, Gemini, persistence, investor rankings, web export, and Telegram steps continue.
5. FRED observations and macro snapshot are persisted after event intelligence persistence.
6. `web/data/latest-report.json` receives an additive `macro` object.

Backward compatibility:

- Existing JSON keys are preserved.
- FRED macro export is additive.
- Existing automation entry point remains unchanged.
- Existing Telegram content was not changed for this FRED phase.

## Sample Macro Output

From `web/data/latest-report.json` after the full validation run:

```json
{
  "source": "FRED",
  "status": "OK",
  "fed_funds_rate": 3.64,
  "fed_funds_date": "2026-04-01",
  "cpi_value": 332.407,
  "cpi_date": "2026-04-01",
  "cpi_yoy": 3.95,
  "cpi_3m_annualized": 7.32,
  "unemployment_rate": 4.3,
  "unemployment_date": "2026-04-01",
  "unemployment_trend": "STABLE",
  "treasury_10y": 4.45,
  "treasury_10y_date": "2026-05-28",
  "treasury_2y": 3.99,
  "treasury_2y_date": "2026-05-28",
  "yield_curve_spread": 0.46,
  "yield_curve_state": "NORMAL",
  "interest_rate_trend": "STABLE",
  "inflation_trend": "REACCELERATING",
  "macro_regime": "MIXED",
  "macro_risk_score": 65,
  "errors": {},
  "summary": "Macro regime is MIXED. Inflation trend is REACCELERATING, interest rate trend is STABLE, and the yield curve is NORMAL with a 10Y-2Y spread of 0.46%."
}
```

## Tests Added

Added collector tests:

- Missing `FRED_API_KEY` returns structured error.
- API observations are fetched and normalized.
- `"."` FRED values normalize to `null`.
- Valid cache files are used instead of issuing requests.
- API keys are redacted from error strings.

Added macro regime tests:

- CPI YoY calculation.
- Reaccelerating inflation trend classification.
- Inverted yield curve classification.
- Stable/rising interest rate trend logic.
- Compact macro snapshot generation.

Added web export test:

- `latest-report.json` includes the additive compact `macro` object.

## Validation Results

Unit tests:

```text
python3 -m unittest app.collectors.test_fred_macro
Ran 4 tests in 0.003s
OK

python3 -m unittest app.analytics.test_macro_regime_engine
Ran 5 tests in 0.004s
OK

python3 -m unittest app.renderers.test_web_export
Ran 3 tests in 0.004s
OK

python3 -m unittest discover app
Ran 24 tests in 0.010s
OK
```

JSON validation:

- `web/data/latest-report.json`: valid JSON
- `web/data/investor-rankings.json`: valid JSON
- `web/data/full-report.json`: valid JSON
- `web/data/data-health.json`: valid JSON

Sensitive value validation:

- `rg "api_key=|2f32" web/data` returned no matches.

Full AlphaScope run:

```text
.venv/bin/python -m app.main full
AlphaScope completed successfully in 61.74s
real 64.20
```

Full run persistence output:

```text
Persisted 264 FRED observations
Persisted FRED macro snapshot
Web exports complete.
Telegram executive summary delivered.
```

## Runtime Impact

Observed FRED collection interval during the full run:

- Start: `19:02:08.473`
- Next pipeline step: `19:02:09.891`
- Approximate FRED collection impact: `1.4s`

Observed full run:

- AlphaScope internal runtime: `61.74s`
- Wall-clock runtime: `64.20s`

FRED adds a small network-bound step. Cache hits should reduce later FRED collection overhead further, subject to configured cache TTL.

## Notes

- FRED was integrated as a macro context and persistence layer only.
- Gemini prompts were not changed.
- Dashboard UI was not changed.
- Telegram format was not changed for this FRED phase.
- Existing FMP-limited symbol coverage behavior remains unchanged and is unrelated to FRED.
