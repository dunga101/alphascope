# AlphaScope FRED Macro Intelligence Integration Plan

Status: planning only. No code changes have been made.

## 1. Architecture Review

AlphaScope currently has two macro-style paths:

- `app/collectors/macro.py`
  - Uses `yfinance` to collect 5-day market context for symbols such as `^GSPC`, `^IXIC`, `^DJI`, `^VIX`, `^TNX`, gold, oil, and Bitcoin.
  - Output is passed to Telegram summary and Gemini market analysis.

- `app/collectors/macro_signals.py`
  - Uses `yfinance` to collect tactical market signals such as VIX, 10-year yield proxy, and sector ETF changes.
  - Feeds the technical report regime fusion path through `app/renderers/report.py`.

Current gaps:

- No durable macroeconomic time-series persistence for inflation, labor, Fed policy, or Treasury curve data.
- Existing macro context is market-price driven, not economic-data driven.
- Existing dashboard does not expose a structured macro regime.
- Existing Telegram summary only reports short market symbol moves, not economic macro context.

FRED should be added as an additional macroeconomic context layer, not a replacement for current `yfinance` market context.

Recommended integration model:

```text
FRED API
  -> FRED collector
  -> macro observations persistence
  -> macro intelligence derivation
  -> macro snapshot persistence/export
  -> Gemini context, dashboard, Telegram
```

Do not modify Gemini architecture in the first FRED sprint. Treat FRED output as structured context that can be included in the existing market analysis prompt later, after deterministic collection and export are stable.

## 2. Proposed Database Schema

Use two tables:

1. Raw normalized observations.
2. Derived per-run macro snapshot.

### `fred_observations`

Purpose: durable economic time-series store.

```sql
CREATE TABLE IF NOT EXISTS fred_observations (
    id SERIAL PRIMARY KEY,
    series_id VARCHAR(32) NOT NULL,
    observation_date DATE NOT NULL,
    value DOUBLE PRECISION,
    realtime_start DATE,
    realtime_end DATE,
    source VARCHAR(20) NOT NULL DEFAULT 'FRED',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    raw_observation JSONB,
    UNIQUE (series_id, observation_date)
);

CREATE INDEX IF NOT EXISTS idx_fred_observations_series_date
ON fred_observations (series_id, observation_date DESC);
```

Tracked series:

| Series ID | Name | Frequency | Notes |
|---|---|---|---|
| `FEDFUNDS` | Effective Federal Funds Rate | Monthly | Policy rate context |
| `CPIAUCSL` | CPI for All Urban Consumers | Monthly | Inflation trend |
| `UNRATE` | Unemployment Rate | Monthly | Labor market trend |
| `DGS10` | 10-Year Treasury Constant Maturity Rate | Daily business days | Long-rate context |
| `DGS2` | 2-Year Treasury Constant Maturity Rate | Daily business days | Front-end rate context |

### `macro_snapshots`

Purpose: one derived macro intelligence row per AlphaScope run/date.

```sql
CREATE TABLE IF NOT EXISTS macro_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    fed_funds_rate DOUBLE PRECISION,
    cpi_value DOUBLE PRECISION,
    cpi_yoy DOUBLE PRECISION,
    cpi_3m_trend VARCHAR(30),
    unemployment_rate DOUBLE PRECISION,
    unemployment_trend VARCHAR(30),
    treasury_10y DOUBLE PRECISION,
    treasury_2y DOUBLE PRECISION,
    yield_curve_spread DOUBLE PRECISION,
    yield_curve_state VARCHAR(30),
    interest_rate_trend VARCHAR(30),
    inflation_trend VARCHAR(30),
    macro_regime VARCHAR(50),
    macro_risk_score DOUBLE PRECISION,
    summary TEXT,
    raw_macro JSONB,
    UNIQUE (snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_macro_snapshots_date
ON macro_snapshots (snapshot_date DESC);
```

Example enum-style values:

- `inflation_trend`: `COOLING`, `STABLE`, `REACCELERATING`, `UNKNOWN`
- `interest_rate_trend`: `FALLING`, `STABLE`, `RISING`, `UNKNOWN`
- `yield_curve_state`: `NORMAL`, `FLAT`, `INVERTED`, `UNKNOWN`
- `macro_regime`: `GOLDILOCKS`, `DISINFLATIONARY_GROWTH`, `STAGFLATION_RISK`, `RECESSION_RISK`, `RESTRICTIVE_POLICY`, `MIXED`, `UNKNOWN`

## 3. Collector Design

### New Collector

Recommended file:

```text
app/collectors/fred_macro.py
```

Responsibilities:

- Load `FRED_API_KEY` from `.env`.
- Fetch recent observations for each required series.
- Normalize FRED values into floats.
- Handle missing value marker `"."`.
- Cache raw responses locally.
- Return a structured payload independent of database persistence.

Recommended FRED endpoint:

```text
https://api.stlouisfed.org/fred/series/observations
```

Request parameters:

```text
series_id=FEDFUNDS
api_key=<FRED_API_KEY>
file_type=json
sort_order=desc
limit=24
```

Recommended per-series limits:

| Series | Recommended Limit | Reason |
|---|---:|---|
| `FEDFUNDS` | 24 | 2 years monthly history |
| `CPIAUCSL` | 36 | YoY and 3-month trend calculations |
| `UNRATE` | 24 | labor trend context |
| `DGS10` | 90 | recent daily trend |
| `DGS2` | 90 | recent daily curve state |

### Cache Design

Recommended cache directory:

```text
data/cache/fred/
```

Files:

```text
data/cache/fred/FEDFUNDS.json
data/cache/fred/CPIAUCSL.json
data/cache/fred/UNRATE.json
data/cache/fred/DGS10.json
data/cache/fred/DGS2.json
```

Recommended TTL:

- Monthly series: 12 hours.
- Daily Treasury series: 6 hours.

Environment variables:

```text
FRED_API_KEY=
FRED_CACHE_HOURS=6
FRED_MONTHLY_CACHE_HOURS=12
```

### Collector Output Shape

```json
{
  "status": "OK",
  "source": "FRED",
  "series": {
    "FEDFUNDS": {
      "latest": {
        "date": "2026-05-01",
        "value": 4.33
      },
      "observations": []
    }
  },
  "errors": {},
  "cache_stats": {
    "hits": 0,
    "misses": 5
  }
}
```

### Derivation Layer

Recommended file:

```text
app/analytics/macro_regime_engine.py
```

Responsibilities:

- Calculate inflation trend from CPI.
- Calculate interest rate trend from Fed Funds plus Treasury yields.
- Calculate yield curve state from `DGS10 - DGS2`.
- Determine macro regime.
- Produce deterministic summary and risk score.

Required derived metrics:

#### Inflation Trend

Inputs:

- `CPIAUCSL` latest value.
- CPI value 12 months ago.
- CPI values from latest 3 months.

Calculations:

- `cpi_yoy = (latest / value_12_months_ago - 1) * 100`
- 3-month annualized trend if enough data is available.

Suggested classification:

- `COOLING`: YoY falling and 3-month annualized trend below prior YoY.
- `REACCELERATING`: YoY rising or 3-month annualized trend meaningfully above prior YoY.
- `STABLE`: small changes around prior trend.
- `UNKNOWN`: insufficient data.

#### Interest Rate Trend

Inputs:

- `FEDFUNDS`
- `DGS10`
- `DGS2`

Suggested classification:

- `RISING`: latest Fed Funds or 2Y yield materially above 3-month average.
- `FALLING`: latest Fed Funds or 2Y yield materially below 3-month average.
- `STABLE`: no material change.
- `UNKNOWN`: insufficient data.

#### Yield Curve State

Input:

- `yield_curve_spread = DGS10 - DGS2`

Suggested classification:

- `INVERTED`: spread < -0.25
- `FLAT`: -0.25 <= spread <= 0.25
- `NORMAL`: spread > 0.25
- `UNKNOWN`: missing yield data.

#### Macro Regime

Initial deterministic rules:

| Conditions | Regime |
|---|---|
| Inflation cooling, unemployment stable/falling, curve normal | `GOLDILOCKS` |
| Inflation cooling, rates falling, unemployment rising | `DISINFLATIONARY_GROWTH` or `RECESSION_RISK` depending labor trend |
| Inflation reaccelerating and unemployment rising | `STAGFLATION_RISK` |
| Inflation reaccelerating and rates rising | `RESTRICTIVE_POLICY` |
| Yield curve inverted and unemployment rising | `RECESSION_RISK` |
| Mixed signals | `MIXED` |

## 4. API Usage Estimate

FRED API call count is small and predictable.

### Per Full AlphaScope Run

Cold cache:

```text
5 FRED API calls
```

Warm cache:

```text
0 FRED API calls
```

### Three Runs Per Day

With recommended TTLs:

- Monthly series may fetch 1-2 times/day.
- Daily Treasury series may fetch up to 3 times/day depending schedule and TTL.

Expected daily calls:

```text
5 to 15 calls/day
```

This is low relative to FMP and Yahoo Finance usage.

### Failure Behavior

Collector should be non-fatal:

- Missing `FRED_API_KEY`: return `status = ERROR`, skip persistence, keep AlphaScope run alive.
- FRED timeout/rate-limit/error: record errors by series, use cache if valid or stale fallback if available.
- Partial FRED data: derive only available metrics and mark unknown fields as `UNKNOWN`.

## 5. Storage Requirements

Raw observation storage is small.

Initial backfill estimate:

| Series | Rows |
|---|---:|
| `FEDFUNDS` | 24 |
| `CPIAUCSL` | 36 |
| `UNRATE` | 24 |
| `DGS10` | 90 |
| `DGS2` | 90 |
| Total | 264 |

Ongoing annual growth:

| Series Type | Rows/year |
|---|---:|
| 3 monthly series | about 36 |
| 2 daily business-day series | about 504 |
| Macro snapshots | about 365 if daily |
| Total | about 905 rows/year |

Storage impact is negligible for PostgreSQL.

Recommended retention:

- Keep all `fred_observations`.
- Keep all `macro_snapshots`.
- These tables are small and valuable for historical regime analysis.

## 6. Dashboard Integration Proposal

### Static JSON Export

Add a new export:

```text
web/data/macro-health.json
```

or include in existing:

```text
web/data/latest-report.json
```

Recommended first sprint:

- Add a compact `macro` object to `latest-report.json`.
- Optionally add `web/data/macro-context.json` if detailed history is needed.

Suggested `latest-report.json` addition:

```json
{
  "macro": {
    "macro_regime": "RESTRICTIVE_POLICY",
    "inflation_trend": "COOLING",
    "interest_rate_trend": "STABLE",
    "yield_curve_state": "INVERTED",
    "fed_funds_rate": 4.33,
    "cpi_yoy": 3.1,
    "unemployment_rate": 4.0,
    "treasury_10y": 4.45,
    "treasury_2y": 4.75,
    "yield_curve_spread": -0.30,
    "summary": "Inflation is cooling, but policy remains restrictive and the yield curve is inverted."
  }
}
```

### Homepage

Add a Macro Regime card near Market Snapshot:

- Macro Regime
- Inflation Trend
- Interest Rate Trend
- Yield Curve State

Keep it compact. The homepage should still prioritize investor rankings.

### Data Health Page

Extend `web/health.html` later with FRED series health:

- Series ID
- Latest observation date
- Latest value
- Cache status
- Last successful collection
- Status

### Analyst Dashboard

Add a Macro Intelligence section:

- Fed policy rate.
- CPI YoY.
- Unemployment.
- 10Y/2Y spread.
- Regime explanation.

Avoid charting in the first sprint unless a lightweight table is insufficient.

## 7. Telegram Integration Proposal

Add a concise macro block to the existing Telegram summary.

Example:

```text
MACRO
Regime: RESTRICTIVE_POLICY
Inflation: COOLING | Rates: STABLE | Curve: INVERTED
Fed Funds: 4.33% | CPI YoY: 3.1% | Unemployment: 4.0%
10Y/2Y: -0.30%
```

Rules:

- Keep under existing Telegram size limits.
- If FRED is unavailable, send:

```text
MACRO
FRED macro context unavailable.
```

Do not add Gemini-generated macro text to Telegram in the first implementation. Use deterministic summary text from the macro regime engine.

## 8. Risks And Dependencies

### Dependencies

- FRED API key.
- Network access from automation host.
- PostgreSQL migration applied before persistence.
- Cache directory writable by automation user.

### Risks

#### Data Release Lag

CPI, Fed Funds, and unemployment update monthly. Dashboard users may expect daily changes. UI should display observation dates.

Mitigation:

- Always show latest observation date.
- Label daily versus monthly series clearly.

#### Missing Values

FRED may return `"."` for missing observations.

Mitigation:

- Normalize `"."` to `None`.
- Exclude missing values from trend calculations.

#### False Precision

Macro regime rules can overstate confidence.

Mitigation:

- Use `MIXED` or `UNKNOWN` when signals conflict.
- Include a deterministic macro risk score but avoid pretending it is predictive.

#### Prompt Bloat

Adding raw FRED observations to Gemini could increase token usage.

Mitigation:

- Pass only the derived macro snapshot and latest values to Gemini, not full time series.

#### Schema Duplication

Existing `market_snapshots` has fields like `us10y`, but it is not a suitable economic time-series store.

Mitigation:

- Use `fred_observations` and `macro_snapshots`.
- Do not overload `market_snapshots`.

#### Automation Failures

FRED failures should not break the full AlphaScope run.

Mitigation:

- Collector returns structured errors.
- Persistence is best-effort.
- Web export handles missing macro context.

## 9. Recommended Implementation Order

### Phase 1: Planning And Configuration

1. Add `FRED_API_KEY` to environment documentation.
2. Confirm FRED API access from automation host.
3. Add FRED cache directory convention.

### Phase 2: Database Migration

1. Add `fred_observations`.
2. Add `macro_snapshots`.
3. Add indexes.
4. Add persistence helpers.

### Phase 3: Collector

1. Implement `app/collectors/fred_macro.py`.
2. Add cache handling.
3. Add request timeout and error handling.
4. Add unit tests with mocked FRED responses.

### Phase 4: Macro Regime Engine

1. Implement inflation trend calculation.
2. Implement interest rate trend calculation.
3. Implement yield curve state.
4. Implement macro regime classification.
5. Add focused tests for edge cases:
   - inverted curve
   - missing CPI
   - cooling inflation
   - rising unemployment
   - partial FRED data.

### Phase 5: Pipeline Integration

1. Collect FRED after existing `macro_context`.
2. Persist raw observations.
3. Build and persist macro snapshot.
4. Add macro snapshot to `build_full_report()` return payload.
5. Keep failures non-fatal.

### Phase 6: Web Export

1. Add compact macro object to `latest-report.json`.
2. Optionally export `web/data/macro-context.json`.
3. Validate JSON output.

### Phase 7: Dashboard

1. Add Macro Regime card to homepage.
2. Add Macro Intelligence section to Analyst Dashboard.
3. Add FRED health rows to Data Health page if needed.

### Phase 8: Telegram

1. Add deterministic macro block to Telegram summary.
2. Preserve existing Telegram sections.
3. Verify message length.

### Phase 9: Validation

Run:

```bash
python3 -m unittest discover app
python3 -m json.tool web/data/latest-report.json
python3 -m json.tool web/data/data-health.json
```

Full-cycle validation:

```bash
/usr/bin/time -p .venv/bin/python -m app.main full
```

Acceptance criteria:

- FRED collector returns all five required series or clear per-series errors.
- `fred_observations` persists latest observations idempotently.
- `macro_snapshots` persists one snapshot per run/date.
- Dashboard shows macro regime without breaking existing investor dashboard.
- Telegram includes concise macro block.
- AlphaScope run remains successful if FRED is unavailable.
