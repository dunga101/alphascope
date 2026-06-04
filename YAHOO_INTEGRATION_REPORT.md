# AlphaScope V1.2 Yahoo Integration Report

Generated: 2026-06-04

## Executive Summary

Yahoo Finance fundamentals integration is implemented and validated.

Result:

- Investor universe expanded from 25 to 50 symbols.
- Full pipeline completed successfully.
- `fundamental_snapshots`: 50/50 symbols persisted for the current run.
- `investor_scores`: 50/50 symbols persisted for the current run.
- Previously affected FMP-402 symbols now receive PE, ROE, and dividend yield from Yahoo.
- The default `47.25` missing-fundamentals path is no longer used as a normal recommendation path.
- Missing critical fundamentals now produce `Insufficient Data`.
- Dashboard formatters now render missing numeric values as `N/A` instead of `0` / `0%`.
- Telegram executive summary was delivered during the full pipeline run.

## Architecture Changes

### Before

```text
FMP fundamentals
  -> in-memory fundamentals
  -> fundamental_snapshots
  -> investor scoring
  -> investor_scores
  -> web/data/*.json
  -> dashboard
```

FMP failures removed symbols from the fundamentals map, but the ranking engine still scored them with default component scores.

### After

```text
FMP fundamentals        Yahoo fundamentals
       |                       |
       +----------+------------+
                  |
                  v
        field-level merge layer
        FMP wins when valid
        Yahoo fills missing fields
                  |
                  v
      merged fundamentals source of truth
                  |
                  v
  provenance + completeness persistence
                  |
                  v
      scoring with data-status gating
                  |
                  v
   enhanced data-health / rankings JSON
                  |
                  v
     dashboard N/A rendering + quality badges
```

## Provider Precedence

Implemented field-level precedence:

```text
if FMP value is valid:
    use FMP
elif Yahoo value is valid:
    use Yahoo
else:
    value = null, source = UNKNOWN
```

The final merged fundamentals payload is the source of truth for persistence, scoring, export, and data-health.

## Coverage Statistics

From the successful full run on 2026-06-04:

| Metric | Result |
|---|---:|
| Investor universe | 50 symbols |
| Fundamentals persisted | 50/50 |
| Investor scores persisted | 50/50 |
| Yahoo coverage | 50/50 |
| FMP coverage | 27/50 |
| Combined FMP/Yahoo symbols | 27 |
| Yahoo-only symbols | 23 |
| FMP-only symbols | 0 |
| Symbols with completeness >= 75% | 50 |
| Symbols with completeness = 100% | 41 |

Investor score data status:

| Status | Count |
|---|---:|
| COMPLETE | 41 |
| PARTIAL | 5 |
| INSUFFICIENT_DATA | 4 |

`data-health.json` metric coverage:

| Metric | Available | FMP | Yahoo | Missing |
|---|---:|---:|---:|---:|
| PE Ratio | 49 | 27 | 22 | 1 |
| ROE | 48 | 27 | 21 | 2 |
| Dividend Yield | 48 | 27 | 21 | 2 |

## Affected Symbol Validation

Previously affected symbols now have complete Yahoo fundamentals:

| Symbol | PE Ratio | PE Source | ROE | ROE Source | Dividend Yield | Dividend Source | Provider | Completeness |
|---|---:|---|---:|---|---:|---|---|---:|
| AVGO | 80.0050 | YAHOO | 0.3337 | YAHOO | 0.005400 | YAHOO | YAHOO | 100% |
| IBM | 27.0230 | YAHOO | 0.3577 | YAHOO | 0.022100 | YAHOO | YAHOO | 100% |
| LLY | 38.2546 | YAHOO | 1.0746 | YAHOO | 0.006400 | YAHOO | YAHOO | 100% |
| MA | 27.3204 | YAHOO | 2.3208 | YAHOO | 0.007400 | YAHOO | YAHOO | 100% |
| MRK | 32.2191 | YAHOO | 0.1894 | YAHOO | 0.029600 | YAHOO | YAHOO | 100% |
| ORCL | 41.3519 | YAHOO | 0.5757 | YAHOO | 0.008700 | YAHOO | YAHOO | 100% |
| PG | 20.4956 | YAHOO | 0.3111 | YAHOO | 0.030400 | YAHOO | YAHOO | 100% |

Investor score validation:

| Symbol | Buy Score | Recommendation | Data Status | Provider |
|---|---:|---|---|---|
| AVGO | 58.15 | Watch | COMPLETE | YAHOO |
| IBM | 65.10 | Buy | COMPLETE | YAHOO |
| LLY | 63.15 | Watch | COMPLETE | YAHOO |
| MA | 62.10 | Watch | COMPLETE | YAHOO |
| MRK | 70.80 | Buy | COMPLETE | YAHOO |
| ORCL | 44.25 | Avoid | COMPLETE | YAHOO |
| PG | 76.65 | Buy | COMPLETE | YAHOO |

None of these symbols used the old default `47.25` score path.

## Affected Files

Created:

- `app/collectors/yahoo_fundamentals.py`
- `app/collectors/fundamentals_provider.py`
- `app/collectors/test_yahoo_fundamentals.py`
- `app/collectors/test_fundamentals_provider.py`
- `app/db/migrate_yahoo_fundamentals_v12.sql`

Modified:

- `app/main.py`
- `app/collectors/fmp_fundamentals.py`
- `app/analytics/investor_ranking.py`
- `app/analytics/investor_scoring_engine.py`
- `app/analytics/test_investor_scoring_engine.py`
- `app/db/intelligence_persistence.py`
- `app/db/schema_intelligence.sql`
- `app/renderers/web_export.py`
- `app/config/symbols.py`
- `app/test_investor_symbol_coverage.py`
- `config/watchlist.yaml`
- `web/index.html`
- `web/opportunity.html`
- generated `web/data/*.json`

Not modified:

- Cloudflare deployment logic
- Telegram delivery logic
- Automation timers

## Database Changes

Applied additive migration:

- `app/db/migrate_yahoo_fundamentals_v12.sql`

Added nullable provenance/completeness fields to `fundamental_snapshots`, including:

- `provider_used`
- `providers_available`
- `pe_ratio_source`
- `roe_source`
- `dividend_yield_source`
- `debt_to_equity_source`
- `free_cash_flow_source`
- `market_cap`
- `market_cap_source`
- `sector`
- `industry`
- `data_completeness_percent`
- `available_fields`
- `missing_fields`
- `provider_errors`
- `raw_provider_data`

Existing rows were backfilled with source-based defaults where applicable.

## Test Results

Unit tests:

```text
.venv/bin/python -m unittest discover app
Ran 33 tests
OK
```

Full pipeline:

```text
.venv/bin/python -m app.main full
AlphaScope completed successfully in 96.82s
Persisted 50 fundamental snapshots
Persisted 50 investor score snapshots
Web dashboard JSON exported.
Telegram executive summary delivered.
```

JSON validation:

```text
python3 -m json.tool web/data/latest-report.json
python3 -m json.tool web/data/investor-rankings.json
python3 -m json.tool web/data/data-health.json
```

All three JSON files are valid.

## Notes And Residual Risks

- FMP quote coverage was 27/50 in the latest run. This does not block Yahoo fundamentals coverage, but some dashboard quote fields remain unavailable for non-FMP quote symbols.
- Technical snapshots remain limited by the existing technical report universe; expanded symbols without technical snapshots are marked partial in `data-health.json`.
- Four symbols were marked `INSUFFICIENT_DATA` because Yahoo lacked one or more critical scoring fields: `CRWD`, `PANW`, `MCD`, `LOW`.
- Yahoo dividend yield scale varied by response shape; the collector now normalizes percent-style yields to decimal form.
- `yfinance` is an unofficial Yahoo interface and should be monitored for response changes.

## Outcome

Success criteria status:

- Operates without relying solely on FMP fundamentals: achieved.
- Affected symbols receive valid fundamentals: achieved.
- Missing values display as `N/A`: implemented.
- Data quality is visible: implemented.
- Universe expanded to 50 symbols: achieved.
- Combined fundamentals coverage exceeds 95%: achieved, 50/50.
- Investor rankings use real fundamentals when available: achieved.
