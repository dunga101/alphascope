# AlphaScope Sprint 1A Results

Date: 2026-06-01

## Implementation Summary

Completed Sprint 1A scope:

- Expanded Investor Edition universe from 7 to 25 symbols.
- Added explicit `investor` watchlist group in `config/watchlist.yaml`.
- Updated `CORE_SYMBOLS`, `FMP_WATCHLIST`, and `FUNDAMENTAL_SYMBOLS` for the 25-symbol rollout.
- Added `current_price` to investor scoring output and persisted score metadata.
- Extended `investor-rankings.json` rows with:
  - company
  - sector
  - current price
  - dividend yield
  - score breakdown
  - missing-data notes
- Added `top_opportunities` to `latest-report.json` while preserving existing top-level fields.
- Redesigned `web/index.html` around:
  - Market Snapshot
  - Top Opportunities
  - Investor Rankings
  - Buy Score tooltip
  - Buy Score breakdown modal
- Re-labeled `web/intelligence.html` as Analyst Dashboard.
- Added Top Opportunities output to the Telegram summary.

Not changed:

- Gemini architecture.
- External API providers.
- Automation output file set.
- Existing JSON export filenames.
- Broker/portfolio/auth functionality.

## Universe

Sprint 1A investor universe size: 25 symbols.

Symbols:

```text
AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA,
AVGO, AMD, ORCL, CSCO, IBM,
JPM, BAC, V, MA,
UNH, JNJ, LLY, MRK,
XOM, CVX,
PG, KO, PEP
```

## Tests Executed

Focused tests:

```bash
python3 -m unittest app.analytics.test_investor_scoring_engine
python3 -m unittest app.renderers.test_web_export
python3 -m unittest app.test_investor_symbol_coverage
```

Result:

```text
app.analytics.test_investor_scoring_engine: 2 tests passed
app.renderers.test_web_export: 1 test passed
app.test_investor_symbol_coverage: 3 tests passed
```

Full discovered app tests:

```bash
python3 -m unittest discover app
```

Result:

```text
Ran 13 tests in 0.006s
OK
```

Note: test discovery emitted an existing `datetime.utcnow()` deprecation warning from `app/collectors/finnhub_news.py`.

## Full AlphaScope Cycle

Command:

```bash
/usr/bin/time -p .venv/bin/python -m app.main full
```

Initial sandboxed run:

- Failed due DNS/network restrictions in the sandbox.
- Failure occurred while reaching external services, including Yahoo/Finnhub/Gemini.
- Runtime before failure: 57.07 seconds.

Escalated network run:

- Completed successfully.
- AlphaScope logged runtime: 71.7 seconds.
- Wall-clock runtime from `/usr/bin/time`: 74.27 seconds.

Key run output:

```text
Persisted 10 technical snapshots
Persisted 18 fundamental snapshots
Persisted 25 investor score snapshots
Web exports complete.
Telegram executive summary delivered.
```

Observed data caveat:

- 25 investor score rows were generated and persisted.
- 18 fundamental snapshots were persisted because some expanded-universe fundamentals were unavailable from the current FMP collection/cache state.
- Several symbols did not have DB-backed technical price history, so investor ranking used conservative technical fallback behavior for those names.

## Generated Output Validation

Validated:

```bash
python3 -m json.tool web/data/latest-report.json
python3 -m json.tool web/data/investor-rankings.json
python3 -m json.tool web/data/full-report.json
```

Result:

```text
All generated JSON files parsed successfully.
```

Investor rankings payload:

```text
count: 25
actual rankings length: 25
```

Top opportunities from generated payload:

```text
1. KO   | Score 80.40 | Strong Buy | Dividend Yield 2.62%
2. META | Score 76.50 | Buy        | Dividend Yield 0.33%
3. BAC  | Score 76.05 | Buy        | Dividend Yield 2.13%
4. PEP  | Score 75.60 | Buy        | Dividend Yield 4.00%
5. XOM  | Score 74.40 | Buy        | Dividend Yield 2.75%
```

`latest-report.json` now includes `top_opportunities` with 5 entries.

## Runtime Measurement

Measured successful full-cycle runtime:

```text
AlphaScope logged runtime: 71.7 seconds
Wall-clock runtime: 74.27 seconds
```

Compared with previous 7-symbol warm-cache runs from logs:

```text
29.06 seconds
34.16 seconds
32.22 seconds
```

Sprint 1A runtime increased materially, mostly from the expanded per-symbol earnings/FMP/fundamental work and live external API latency.

## Backward Compatibility

Preserved:

- `web/data/latest-report.json`
- `web/data/full-report.json`
- `web/data/investor-rankings.json`
- Existing top-level `latest-report.json` fields:
  - `generated_at`
  - `generated_at_iso`
  - `generation_status`
  - `regime`
  - `confidence`
  - `summary`
  - `bullish`
  - `bearish`
  - `ticker`
- Existing `full-report.json` `full_report` field.
- Existing automation generated file set.

Additive changes:

- `latest-report.json.top_opportunities`
- `investor-rankings.json` row fields:
  - `current_price`
  - `missing_data`
  - `score_breakdown`

## Follow-Up Risks

- Some expanded symbols lack market price history in PostgreSQL, limiting technical score completeness.
- Some expanded symbols did not persist fundamentals in the successful run.
- Current runtime is acceptable for 25 symbols but should be monitored before any move to 50.
- The homepage now depends on enriched ranking fields, but it still handles missing values with `--`.
