# Phase 2 Investor Edition Implementation Notes

## Summary

Phase 2 adds an additive Investor Edition ranking path without changing the existing intelligence, AI synthesis, technical report, dashboard, ranking, or recommendation behavior used by the current AlphaScope workflow.

## Added Modules

- `app/analytics/investor_scoring_engine.py`
  - Scores each symbol across:
    - valuation
    - dividend
    - financial quality
    - price position
    - technicals
  - Produces `buy_score` from 0-100.
  - Applies Investor Edition recommendation labels:
    - `Strong Buy`
    - `Buy`
    - `Watch`
    - `Avoid`

- `app/analytics/investor_ranking.py`
  - Loads tracked symbols from `config/watchlist.yaml`.
  - Uses `investor` group when present, otherwise falls back to `core`.
  - Reuses collected FMP fundamentals, company profiles, and quotes.
  - Reuses existing DB-backed technical indicators from `app.analytics.technical_engine`.
  - Sorts ranked opportunities by highest `buy_score`.
  - Handles missing technical data by logging a warning and continuing.

## Persistence

- Added `persist_investor_score()` and `persist_investor_scores()` to `app/db/intelligence_persistence.py`.
- Added `investor_scores` DDL to `app/db/schema_intelligence.sql`.
- Persistence uses upsert semantics on `(score_date, symbol)`.
- Main pipeline catches investor persistence errors so a missing new table cannot break existing intelligence report generation.

## Pipeline Integration

- `app/main.py` now:
  - carries raw `company_profiles` out of `collect_fmp_layer()`.
  - builds investor rankings after fundamentals are persisted.
  - persists investor scores when possible.
  - returns `investor_rankings` in the `build_full_report()` result payload.

Existing report text, Telegram summary, dashboard export, AI prompts, technical report generation, and recommendation logic were not changed.

## Tests

Added focused tests:

- `app/analytics/test_investor_scoring_engine.py`
  - Verifies Investor Edition recommendation thresholds.
  - Verifies scoring output shape and key dashboard fields.

- `app/db/test_investor_persistence.py`
  - Verifies `investor_scores` SQL upsert and parameter mapping.

Existing Phase 1 tests remain unchanged.

## Operational Notes

- Apply `app/db/schema_intelligence.sql` or otherwise create `investor_scores` before expecting investor score rows to persist.
- If the table is absent, AlphaScope logs a warning and continues the existing intelligence flow.
- Symbols without fundamentals or technical data still receive a conservative score so one incomplete symbol does not abort the ranking.
