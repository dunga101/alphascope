# AlphaScope Sprint 1B Results

Date: 2026-06-01

## Implementation Summary

Completed Sprint 1B Data Quality & Coverage Dashboard scope:

- Added `web/data/data-health.json`.
- Added `web/health.html`.
- Added homepage Data Quality summary card.
- Added automated validation coverage for `data-health.json`.
- Added warning logic for:
  - fundamentals coverage below symbol count
  - score coverage below symbol count
  - complete coverage below 95%
- Preserved existing JSON outputs and automation.

## Data Health Payload

Generated sample:

```text
web/data/data-health.json
```

Generated summary:

```text
Total Symbols: 25
Complete Symbols: 14
Partial Symbols: 11
Missing Symbols: 0
Coverage Percentage: 56.0%
Quotes Available: 18
Fundamentals Available: 18
Scores Available: 25
```

Warnings:

```text
Fundamentals coverage below symbol count: 18/25.
Complete coverage below 95%: 56.0%.
```

## Tests Executed

Focused tests:

```bash
python3 -m unittest app.renderers.test_web_export
python3 -m unittest app.analytics.test_investor_scoring_engine
python3 -m unittest app.test_investor_symbol_coverage
```

Result:

```text
app.renderers.test_web_export: 2 tests passed
app.analytics.test_investor_scoring_engine: 2 tests passed
app.test_investor_symbol_coverage: 3 tests passed
```

Full discovered app tests:

```bash
python3 -m unittest discover app
```

Result:

```text
Ran 14 tests in 0.007s
OK
```

Automation script syntax:

```bash
bash -n scripts/alphascope_refresh.sh
```

Result:

```text
OK
```

## Full AlphaScope Run

Command:

```bash
/usr/bin/time -p .venv/bin/python -m app.main full
```

Result:

```text
AlphaScope completed successfully in 59.87s
real 62.82
```

Run output included:

```text
Persisted 10 technical snapshots
Persisted 18 fundamental snapshots
Persisted 25 investor score snapshots
Web exports complete.
Telegram executive summary delivered.
```

## JSON Validation

Validated:

```bash
python3 -m json.tool web/data/latest-report.json
python3 -m json.tool web/data/investor-rankings.json
python3 -m json.tool web/data/full-report.json
python3 -m json.tool web/data/data-health.json
```

Result:

```text
All generated JSON files parsed successfully.
```

## Current Diagnosis

The health export explains the current Sprint 1A coverage gap:

- All 25 investor symbols have investor scores.
- 18 of 25 symbols have fundamentals available in the current run.
- 18 of 25 symbols have quotes available in the current run.
- 14 of 25 symbols are complete across quote, profile, ratios, income, balance, cash flow, technical snapshot, fundamentals, and score.
- 11 symbols are partial, mostly due missing quote/fundamental data or missing DB-backed technical snapshots.

This confirms the new dashboard can identify why symbols are incomplete before expanding beyond 25 symbols.
