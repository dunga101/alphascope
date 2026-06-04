# AlphaScope V1.2 Implementation Plan

Generated: 2026-06-04

## Scope

Implement Yahoo Finance fundamentals as a resilient supplemental provider for AlphaScope Investor Edition and expand the investor universe from 25 symbols to approximately 50 symbols.

This document is a plan only. No implementation changes are included.

## Current Architecture

AlphaScope currently builds Investor Edition rankings from FMP-driven runtime data.

```text
config/watchlist.yaml + app/config/symbols.py
        |
        v
app/main.py
  build_full_report()
        |
        +--> collect_fmp_layer()
        |      |
        |      +--> app/collectors/fmp_quotes.py
        |      +--> app/collectors/fmp_profile.py
        |      +--> app/collectors/fmp_fundamentals.py
        |
        +--> persist_fundamental_results()
        |      |
        |      +--> app/db/intelligence_persistence.py
        |             persist_fundamental_snapshot()
        |             writes fundamental_snapshots
        |
        +--> app/analytics/investor_ranking.py
        |      build_investor_rankings()
        |      |
        |      +--> app/analytics/investor_scoring_engine.py
        |             score_investor_opportunity()
        |
        +--> persist_investor_results()
        |      |
        |      +--> persist_investor_scores()
        |             writes investor_scores
        |
        +--> app/renderers/web_export.py
               export_web_report()
               |
               +--> fetch_latest_investor_rankings()
               +--> web/data/investor-rankings.json
               +--> web/data/data-health.json
               +--> web/data/latest-report.json
        |
        v
web/index.html + web/opportunity.html
  render dashboard from JSON
```

### Existing Collection Flow

- `app/main.py` calls `collect_fmp_layer(mode)`.
- Full mode collects:
  - FMP quotes for `FMP_WATCHLIST`
  - FMP company profiles for `FMP_WATCHLIST`
  - FMP fundamentals for `FUNDAMENTAL_SYMBOLS`
- `app/collectors/fmp_fundamentals.py` fetches:
  - `stable/income-statement`
  - `stable/balance-sheet-statement`
  - `stable/cash-flow-statement`
  - `stable/ratios-ttm`
- The collector maps FMP fields into a flat fundamentals dict with keys such as `pe_ratio`, `dividend_yield`, `roe`, `debt_to_equity`, `free_cash_flow`.
- FMP failures return `{"status": "ERROR", ...}` and are dropped by `collect_fmp_layer()`.

### Existing Persistence Flow

- `persist_fundamental_results(fundamentals)` writes only successful fundamentals.
- `persist_fundamental_snapshot()` writes `fundamental_snapshots` with `source = 'FMP'`.
- `persist_investor_score()` writes `investor_scores`, including score components, `dividend_yield`, `pe_ratio`, and `raw_score`.
- `fetch_latest_investor_rankings()` reads latest `investor_scores` and left-joins latest `fundamental_snapshots` for `roe`, `debt_to_equity`, and `free_cash_flow`.

### Existing Scoring Flow

- `build_investor_rankings()` loads investor symbols from `config/watchlist.yaml`.
- It scores every configured investor symbol even when `fundamentals.get(symbol)` is missing.
- `score_investor_opportunity()` converts missing fundamentals to `{}`.
- Missing PE/dividend/ROE/debt/FCF use default component scores:
  - valuation: `45`
  - dividend: `40`
  - financial quality: `50`
  - price position: `50`
  - technical: `50`
- This default path creates a repeated `47.25` score and `Avoid` recommendation.

### Existing Export Flow

- `export_web_report()` writes:
  - `web/data/latest-report.json`
  - `web/data/full-report.json`
  - `web/data/investor-rankings.json`
  - `web/data/data-health.json`
- `_json_number()` preserves Python `None` as JSON `null`.
- `web/index.html` and `web/opportunity.html` call `Number(value)`, so `null` renders as `0` or `0%`.

## Proposed Architecture

Add Yahoo fundamentals collection and a provider-merge layer. Keep FMP supported and prefer FMP values when valid; use Yahoo per field when FMP is missing, failed, or incomplete.

```text
Expanded symbol universe
  config/watchlist.yaml
  app/config/symbols.py
        |
        v
app/main.py
  collect_market_data_layer()
        |
        +--> FMP collectors
        |      quotes, profiles, fundamentals
        |
        +--> Yahoo fundamentals collector
        |      app/collectors/yahoo_fundamentals.py
        |
        +--> Provider merge layer
               app/collectors/fundamentals_provider.py
               field-level precedence:
                 if valid FMP value: use FMP
                 else if valid Yahoo value: use Yahoo
                 else: None
               emits:
                 merged fundamentals
                 provider metadata
                 completeness metadata
        |
        v
Persistence
  fundamental_snapshots
  provider provenance fields and/or raw metadata
        |
        v
Investor scoring
  complete/partial gating
  Insufficient Data for critical missing fields
        |
        v
Exports
  investor-rankings.json
  data-health.json with provider coverage
        |
        v
Dashboard
  N/A null rendering
  data quality badges
```

## Provider Strategy

### Priority Rule

Use field-level provider precedence:

```python
if fmp_value is valid:
    use fmp_value, source = "FMP"
elif yahoo_value is valid:
    use yahoo_value, source = "YAHOO"
else:
    use None, source = "UNKNOWN"
```

Field-level precedence is preferred over symbol-level precedence because FMP may return partial data. Example: FMP may provide PE while Yahoo provides dividend yield or sector.

### Valid Value Rules

Valid values should be explicit, not truthy-only:

- `None`: invalid.
- Empty strings: invalid.
- Non-numeric text for numeric fields: invalid.
- `0`: valid only for fields where true zero is meaningful, such as dividend yield.
- Negative values: field-specific.
  - negative ROE can be valid and should not be discarded.
  - negative free cash flow can be valid and should inform quality scoring.
  - PE ratio less than or equal to zero is not useful for valuation scoring and should be treated as unavailable or non-meaningful for PE-specific completeness.

## Yahoo Fundamentals Provider

Create `app/collectors/yahoo_fundamentals.py`.

Use `yfinance`, already present in `requirements.txt`.

### Expected Output Shape

The collector should return the same primary keys used by the current scoring/persistence path, plus Yahoo-specific and provenance metadata.

```python
{
    "status": "OK",
    "source": "YAHOO",
    "symbol": "AVGO",
    "cache_status": "MISS",
    "pe_ratio": 34.1,
    "forward_pe": 27.4,
    "dividend_yield": 0.012,
    "roe": 0.58,
    "market_cap": 1900000000000,
    "sector": "Technology",
    "industry": "Semiconductors",
    "revenue": 51500000000,
    "operating_margin": 0.37,
    "net_margin": 0.22,
    "profit_margin": 0.22,
    "beta": 1.1,
    "free_cash_flow": 21000000000,
    "total_debt": 76000000000,
    "debt_to_equity": 1.4,
    "provider_fields": {
        "pe_ratio": "YAHOO",
        "forward_pe": "YAHOO",
        "dividend_yield": "YAHOO",
        "roe": "YAHOO"
    },
    "raw_provider_data": {
        "info_subset": {}
    }
}
```

### Yahoo Field Mapping

Target mappings from `yfinance.Ticker(symbol).get_info()` or `.info`, depending on runtime reliability:

| AlphaScope field | Yahoo candidate key |
|---|---|
| `pe_ratio` | `trailingPE` |
| `forward_pe` | `forwardPE` |
| `dividend_yield` | `dividendYield` |
| `roe` | `returnOnEquity` |
| `market_cap` | `marketCap` |
| `sector` | `sector` |
| `industry` | `industry` |
| `revenue` | `totalRevenue` |
| `operating_margin` | `operatingMargins` |
| `net_margin` / `profit_margin` | `profitMargins` |
| `beta` | `beta` |
| `free_cash_flow` | `freeCashflow` |
| `total_debt` | `totalDebt` |
| `debt_to_equity` | `debtToEquity`, normalized if needed |
| `current_ratio` | `currentRatio` |
| `cash_and_equivalents` | `totalCash` |

Implementation note: Yahoo `debtToEquity` may be expressed as percent-like units in some payloads. The implementation should validate scale against sample outputs before using it directly in scoring.

### Caching

Use a Yahoo-specific cache directory:

```text
data/cache/yahoo_fundamentals/
```

Use an environment variable:

```text
YAHOO_FUNDAMENTAL_CACHE_HOURS=24
```

Cache shape should match collector output. Cache should be considered valid when at least one critical investor field is present or when a recent explicit provider error is cached for a shorter error TTL.

## Provider Merge Layer

Create `app/collectors/fundamentals_provider.py`.

Responsibilities:

- Collect FMP fundamentals.
- Collect Yahoo fundamentals.
- Merge values using provider precedence.
- Calculate data completeness.
- Emit provider coverage diagnostics.
- Preserve backward-compatible fundamentals keys.

Suggested functions:

```python
CRITICAL_FIELDS = ("pe_ratio", "roe", "dividend_yield")
SCORING_FIELDS = ("pe_ratio", "roe", "debt_to_equity", "dividend_yield", "free_cash_flow")

def merge_fundamental_payloads(symbol, fmp_payload, yahoo_payload) -> dict:
    ...

def collect_combined_fundamentals(symbols: list[str]) -> tuple[dict, dict]:
    ...

def calculate_data_completeness(fundamentals: dict) -> dict:
    ...
```

Merged payload example:

```python
{
    "status": "OK",
    "symbol": "AVGO",
    "source": "COMBINED",
    "provider_used": "YAHOO",
    "providers_available": ["YAHOO"],
    "pe_ratio": 34.1,
    "pe_ratio_source": "YAHOO",
    "roe": 0.58,
    "roe_source": "YAHOO",
    "dividend_yield": 0.012,
    "dividend_yield_source": "YAHOO",
    "data_completeness_percent": 83.33,
    "available_fields": ["pe_ratio", "roe", "dividend_yield", "sector", "market_cap"],
    "missing_fields": ["free_cash_flow"],
    "provider_errors": {
        "FMP": "402 Payment Required"
    },
    "raw_provider_data": {
        "fmp": {},
        "yahoo": {}
    }
}
```

## Data Provenance

Track source per major metric in raw data structures and persisted/exported data.

Required source fields:

- `pe_ratio_source`
- `roe_source`
- `dividend_yield_source`

Recommended source fields:

- `debt_to_equity_source`
- `free_cash_flow_source`
- `revenue_source`
- `market_cap_source`
- `sector_source`
- `industry_source`

Allowed values:

- `FMP`
- `YAHOO`
- `UNKNOWN`

## Database Changes

The current `fundamental_snapshots` table has scalar metric columns and a `source` column hard-coded to `FMP` during persistence. The plan should preserve backward compatibility while adding provenance.

### Recommended Migration

Create a non-destructive migration:

```text
app/db/migrate_yahoo_fundamentals_v12.sql
```

Add nullable columns:

```sql
ALTER TABLE fundamental_snapshots
    ADD COLUMN IF NOT EXISTS provider_used VARCHAR(20),
    ADD COLUMN IF NOT EXISTS providers_available JSONB,
    ADD COLUMN IF NOT EXISTS pe_ratio_source VARCHAR(20),
    ADD COLUMN IF NOT EXISTS roe_source VARCHAR(20),
    ADD COLUMN IF NOT EXISTS dividend_yield_source VARCHAR(20),
    ADD COLUMN IF NOT EXISTS debt_to_equity_source VARCHAR(20),
    ADD COLUMN IF NOT EXISTS free_cash_flow_source VARCHAR(20),
    ADD COLUMN IF NOT EXISTS market_cap DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS market_cap_source VARCHAR(20),
    ADD COLUMN IF NOT EXISTS sector VARCHAR(100),
    ADD COLUMN IF NOT EXISTS industry VARCHAR(200),
    ADD COLUMN IF NOT EXISTS data_completeness_percent DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS available_fields JSONB,
    ADD COLUMN IF NOT EXISTS missing_fields JSONB,
    ADD COLUMN IF NOT EXISTS provider_errors JSONB,
    ADD COLUMN IF NOT EXISTS raw_provider_data JSONB;
```

Update `source` semantics:

- Keep existing `source` column for compatibility.
- Store `COMBINED`, `FMP`, or `YAHOO` depending on merged output.
- Do not require old rows to be backfilled.

### Optional Investor Scores Additions

Avoid schema changes to `investor_scores` unless needed. Prefer adding the following inside `raw_score`:

- `data_status`
- `data_quality_label`
- `data_completeness_percent`
- `missing_fundamental_fields`
- `provider_used`
- `metric_sources`

This keeps `investor_scores` backward compatible.

## Scoring Engine Recommendation

Current behavior should be replaced for critical missing fundamentals.

### Proposed Data Statuses

- `COMPLETE`: all scoring fields present.
- `PARTIAL`: enough critical fields are present to compute a real score, but some non-critical fields are missing.
- `INSUFFICIENT_DATA`: critical fundamentals are missing.

### Critical Fields

Minimum critical fields:

- `pe_ratio`
- `roe`
- `dividend_yield`

Recommended scoring fields:

- `pe_ratio`
- `roe`
- `debt_to_equity`
- `dividend_yield`
- `free_cash_flow`

### Recommendation Logic

For `INSUFFICIENT_DATA`:

- Set `recommendation = "Insufficient Data"`.
- Set `buy_score = None` or preserve a diagnostic score outside ranking. Preferred: `buy_score = None` in JSON, but database `investor_scores.buy_score` is `NOT NULL`, so persist `buy_score = 0` only with `raw_score.data_status = "INSUFFICIENT_DATA"` if schema is unchanged.
- Do not rank incomplete symbols alongside complete/partial symbols.

For `PARTIAL`:

- Calculate score using available real fields.
- Include missing field penalties or expose a visible data-quality badge.
- Keep the row ranked below complete rows when score ties occur.

Ranking sort recommendation:

```text
COMPLETE first by buy_score DESC
PARTIAL next by buy_score DESC
INSUFFICIENT_DATA last, unranked or rank = null
```

## Dashboard Improvements

Files:

- `web/index.html`
- `web/opportunity.html`

Planned changes:

- Fix null rendering:
  - `null`, `undefined`, and empty string display as `N/A` or `--`.
  - numeric `0` remains visible as `0` or `0%`.
- Add a data quality badge:
  - `Complete`
  - `Partial`
  - `Insufficient Data`
- Use accessible text labels instead of emoji-only indicators. If icons/colors are used, keep visible text.
- Add source visibility in the opportunity detail view:
  - PE source
  - ROE source
  - dividend source
- Avoid changing Cloudflare deployment logic.

## Data Health Improvements

Enhance `web/data/data-health.json`.

Add top-level summary fields:

```json
{
  "provider_coverage": {
    "fmp_symbols": 18,
    "yahoo_symbols": 49,
    "combined_symbols": 50,
    "total_symbols": 50
  },
  "metric_coverage": {
    "pe_ratio": {
      "available": 49,
      "fmp": 18,
      "yahoo": 31,
      "missing": 1
    },
    "roe": {
      "available": 48,
      "fmp": 18,
      "yahoo": 30,
      "missing": 2
    },
    "dividend_yield": {
      "available": 50,
      "fmp": 18,
      "yahoo": 32,
      "missing": 0
    }
  },
  "missing_symbols": []
}
```

Add per-symbol fields:

- `data_status`
- `data_completeness_percent`
- `provider_used`
- `providers_available`
- `missing_fields`
- `available_fields`
- `pe_ratio_source`
- `roe_source`
- `dividend_yield_source`

## 50 Symbol Expansion

Update both:

- `app/config/symbols.py`
- `config/watchlist.yaml`

Recommended final 50-symbol investor universe:

| Group | Symbols |
|---|---|
| Technology | AAPL, MSFT, NVDA, AMD, AVGO, ORCL, IBM, CSCO, CRM, ADBE |
| AI / Growth | META, AMZN, GOOGL, TSLA, NFLX, PLTR, SNOW, CRWD, PANW, MDB |
| Financials | JPM, BAC, GS, MS, V, MA, AXP, BLK, SCHW |
| Healthcare | LLY, JNJ, MRK, ABBV, UNH, PFE |
| Consumer | KO, PEP, PG, COST, WMT, MCD, HD, LOW |
| Energy / Industrial | XOM, CVX, CAT, DE, LMT, RTX, GE |
| Canadian Exposure | RY, TD, BNS, ENB, CNR |

Count: 50.

Implementation considerations:

- Keep `FMP_WATCHLIST = ["SPY", *CORE_SYMBOLS]` unless FMP quote limits require a separate quote universe.
- Use Yahoo fundamentals for all 50 symbols.
- Keep FMP fundamentals attempted for all 50 initially unless runtime/API usage proves too high; provider diagnostics will show whether to restrict FMP fundamentals later.
- Preserve sector diversification and dividend-oriented coverage.

## Files To Create

- `app/collectors/yahoo_fundamentals.py`
- `app/collectors/fundamentals_provider.py`
- `app/collectors/test_yahoo_fundamentals.py`
- `app/collectors/test_fundamentals_provider.py`
- `app/db/migrate_yahoo_fundamentals_v12.sql`
- `YAHOO_INTEGRATION_REPORT.md` after implementation and validation

## Files To Modify

- `requirements.txt`
  - likely no change required because `yfinance==1.3.0` is already present.
- `app/main.py`
  - replace FMP-only fundamentals collection with combined provider collection.
  - preserve FMP quotes/profile collection.
- `app/collectors/fmp_fundamentals.py`
  - optionally add structured provider error fields and redact API keys in error reasons.
- `app/analytics/investor_ranking.py`
  - sort by data status and score.
  - pass merged fundamentals and metadata through scoring.
- `app/analytics/investor_scoring_engine.py`
  - add missing-critical-field handling.
  - emit data status and missing-field metadata.
- `app/db/intelligence_persistence.py`
  - persist new fundamental provenance/completeness fields.
  - fetch provenance fields for export.
- `app/db/schema_intelligence.sql`
  - reflect additive V1.2 columns for fresh installs.
- `app/renderers/web_export.py`
  - export data status, provider source fields, and provider coverage.
  - improve data-health calculations.
- `app/config/symbols.py`
  - expand `CORE_SYMBOLS`.
- `config/watchlist.yaml`
  - expand `investor` list.
- `web/index.html`
  - null rendering fix.
  - data quality badge in ranking rows/top opportunities.
- `web/opportunity.html`
  - null rendering fix.
  - data quality badge and provider source display.
- Existing tests:
  - `app/collectors/test_fmp_fundamentals.py`
  - `app/analytics/test_investor_scoring_engine.py`
  - `app/db/test_fundamental_persistence.py`
  - `app/db/test_investor_persistence.py`
  - `app/renderers/test_web_export.py`
  - `app/test_investor_symbol_coverage.py`

## Implementation Sequence

1. Add Yahoo collector with caching and unit tests.
2. Add provider merge layer with deterministic field precedence and unit tests.
3. Add database migration and update schema/persistence for provenance fields.
4. Update `app/main.py` to use combined fundamentals while leaving FMP quotes/profiles unchanged.
5. Update scoring engine to classify `INSUFFICIENT_DATA` and prevent default `47.25` rankings.
6. Update ranking sort/group behavior.
7. Expand symbol configuration to 50.
8. Update web export and data-health JSON.
9. Update dashboard null rendering and data quality badges.
10. Run validation and produce `YAHOO_INTEGRATION_REPORT.md`.

## Testing Plan

### Unit Tests

Collector tests:

- Yahoo collector maps `trailingPE`, `forwardPE`, `dividendYield`, `returnOnEquity`, `marketCap`, `sector`, `industry`.
- Yahoo collector returns structured `ERROR` on provider failure.
- Yahoo collector preserves true zero dividend yield.
- Yahoo collector cache hit/miss behavior.

Provider merge tests:

- FMP value wins when both providers have valid values.
- Yahoo fills missing FMP value.
- Per-field source fields are correct.
- Missing fields and available fields are calculated correctly.
- Completeness percent is deterministic.

Scoring tests:

- Complete fundamentals produce normal score/recommendation.
- Missing critical fundamentals produce `Insufficient Data`.
- Affected symbols no longer receive the default `47.25` path when Yahoo data is present.
- True zero dividend yield does not become missing.

Persistence tests:

- New provenance fields are mapped to `fundamental_snapshots`.
- Existing required investor score fields remain backward compatible.
- `raw_score` includes data status and provider metadata.

Export tests:

- `investor-rankings.json` includes provider source fields and data quality status.
- `data-health.json` includes FMP/Yahoo/combined coverage.
- Null numeric values stay JSON `null`.

Dashboard checks:

- `null` metrics display as `N/A` or `--`, not `0`.
- numeric `0` still displays as `0`.
- quality badges display for complete, partial, and insufficient symbols.

### Integration Validation

Run:

```bash
.venv/bin/python -m unittest discover app
```

Run full pipeline in a controlled mode:

```bash
.venv/bin/python -m app.main full
```

Validate JSON:

```bash
python3 -m json.tool web/data/latest-report.json
python3 -m json.tool web/data/investor-rankings.json
python3 -m json.tool web/data/data-health.json
```

Database spot checks:

```sql
SELECT
    symbol,
    pe_ratio,
    pe_ratio_source,
    roe,
    roe_source,
    dividend_yield,
    dividend_yield_source,
    data_completeness_percent,
    provider_used
FROM fundamental_snapshots
WHERE symbol IN ('AVGO','ORCL','IBM','MA','LLY','MRK','PG')
ORDER BY snapshot_date DESC, symbol;
```

```sql
SELECT
    symbol,
    buy_score,
    recommendation,
    raw_score
FROM investor_scores
WHERE symbol IN ('AVGO','ORCL','IBM','MA','LLY','MRK','PG')
ORDER BY score_date DESC, symbol;
```

Required validation symbols:

- `AVGO`
- `ORCL`
- `IBM`
- `MA`
- `LLY`
- `MRK`
- `PG`

Success for these symbols:

- PE ratio populated from FMP or Yahoo.
- Dividend yield populated from FMP or Yahoo, including true zero where appropriate.
- ROE populated where Yahoo provides it.
- No default `47.25` path when real fundamentals are available.
- If a field is unavailable, dashboard shows `N/A`.

### Regression Testing

Confirm:

- Existing 25 symbols still generate rankings.
- Expanded 50-symbol list appears in `data-health.json`.
- Investor rankings still generate.
- Dashboard still renders.
- Telegram report generation still uses the existing summary path.
- Cloudflare deployment files and logic are untouched.
- Automation timer files are untouched.
- Database persistence still writes fundamentals and investor scores.
- `data-health.json` still generates.

## Risks

Yahoo provider reliability:

- `yfinance` can change behavior, throttle, or return incomplete info. Mitigation: cache responses, keep FMP, and track provider errors.

Field scale mismatch:

- Yahoo debt-to-equity and dividend yield scales must be validated. Mitigation: add field-specific normalization tests and sample checks.

Database compatibility:

- Adding columns is low risk, but production migration must be applied before persistence writes new fields. Mitigation: use `ADD COLUMN IF NOT EXISTS` and keep old fields unchanged.

Ranking semantics:

- Introducing `Insufficient Data` changes ranking order and recommendation counts. Mitigation: make status explicit and keep scores backward compatible in persistence if needed.

Runtime/API load:

- Expanding to 50 symbols increases FMP, Yahoo, technical, and profile calls. Mitigation: cache Yahoo fundamentals, consider FMP fundamentals throttling, and keep provider diagnostics.

Dashboard layout:

- New badges/source fields may affect table width. Mitigation: keep compact labels and verify desktop/mobile rendering.

Canadian symbols:

- Yahoo symbols may require suffixes for TSX listings in some contexts. Proposed U.S.-listed ADR/ticker forms `RY`, `TD`, `BNS`, `ENB`, `CNR` should be validated during implementation.

## Rollback Plan

Rollback should be possible without destructive database changes.

1. Revert code changes to:
   - Yahoo collector
   - provider merge integration
   - scoring data-status gating
   - dashboard badges/null rendering
   - symbol expansion
2. Restore previous 25-symbol `CORE_SYMBOLS` and `config/watchlist.yaml` investor list.
3. Leave additive database columns in place; they are nullable and should not affect old code.
4. Re-run the previous FMP-only pipeline.
5. Validate:
   - `web/data/latest-report.json`
   - `web/data/investor-rankings.json`
   - `web/data/data-health.json`
6. Do not revert production data unless explicitly requested; old and new snapshots can coexist by date.

## Deliverables After Approval

Implementation deliverables:

- Yahoo fundamentals collector.
- Combined FMP/Yahoo provider merge.
- Data provenance in raw structures and persistence.
- Data completeness framework.
- Improved scoring behavior for missing fundamentals.
- Dashboard null rendering fix and data quality badges.
- Expanded 50-symbol universe.
- Enhanced `data-health.json`.

Post-implementation report:

- `YAHOO_INTEGRATION_REPORT.md`
  - architecture changes
  - affected files
  - coverage statistics
  - before/after comparison for affected symbols
  - test results
  - coverage improvement metrics

## Approval Gate

Stop here until the implementation plan is approved.
