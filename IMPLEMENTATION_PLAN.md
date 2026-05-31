# AlphaScope Investor Edition Implementation Plan

## 1. Current Architecture Summary

AlphaScope is a Python-based market intelligence pipeline with PostgreSQL persistence, FMP/yfinance data collection, Gemini AI synthesis, Telegram delivery, and a static web dashboard.

Current daily flow:

1. `app/main.py` selects execution mode: `full`, `degraded`, or `offline`.
2. `app/renderers/report.py` generates deterministic technical analysis from a hardcoded watchlist using:
   - `app/processors/indicators.py`
   - `app/processors/screener.py`
   - `app/processors/signal_fusion.py`
   - breadth and macro collectors
3. `app/main.py` collects macro context, sector breadth, earnings context, FMP quotes, FMP company profiles, FMP fundamentals, and news intelligence.
4. Gemini AI produces market and event intelligence unless running in offline mode.
5. `app/processors/confidence_engine.py` merges market and event confidence.
6. Persistence writes:
   - market regime snapshots through `app/db/repositories.py`
   - intelligence reports, event snapshots, and technical snapshots through `app/db/intelligence_persistence.py`
7. `app/renderers/web_export.py` exports JSON payloads to:
   - `web/data/latest-report.json`
   - `web/data/full-report.json`
8. `web/index.html` renders the high-level dashboard.
9. `web/intelligence.html` parses and renders the full report text.
10. Telegram receives an executive summary through `app/renderers/telegram.py`.

There are two technical-analysis paths:

- The active report path uses yfinance in `app/processors/indicators.py` and `app/processors/screener.py`.
- The newer analytics path reads persisted `market_prices` from PostgreSQL through `app/analytics/technical_engine.py` and produces richer signals through `app/analytics/signal_engine.py`.

There is also an existing `app/ai/intelligence_fusion.py` module that already combines technical signals, latest market regime, and latest `fundamental_snapshots` into a per-symbol composite decision-support output. It is not currently wired into the daily run, ranking workflow, or dashboard.

## 2. Existing Reusable Components

The Investor Edition should reuse these existing components before adding new abstractions:

- `app/collectors/fmp_fundamentals.py`
  - Already collects `pe_ratio`, `roe`, `debt_to_equity`, `free_cash_flow`, revenue, income, margins, cash, and debt from FMP.
  - Needs extension for `dividend_yield` and `revenue_growth`.

- `app/collectors/fmp_profile.py`
  - Already collects company name, sector, industry, market cap, beta, exchange, country, description, website, and CEO.
  - Can supply dashboard `Company` and `Sector`.

- `app/collectors/fmp_quotes.py`
  - Already collects price, `yearLow`, `yearHigh`, market cap, 50-day average, 200-day average, and current quote data.
  - Can supply distance from 52-week low if the latest quote payload is available.

- `app/analytics/technical_engine.py`
  - Reads `market_prices` and calculates SMA20, SMA50, SMA200, RSI14, ATR14, 30-day volatility, 52-week drawdown, distance from 52-week low, and relative strength versus SPY.
  - Best reusable source for Investor Edition technical and price-position features.

- `app/analytics/signal_engine.py`
  - Builds structured trend, momentum, volatility, relative-strength, risk-state, signal, confidence, and reasoning.
  - Can feed the Investor Edition technical score.

- `app/ai/intelligence_fusion.py`
  - Already defines dataclasses and scoring helpers for latest fundamentals, market regime, technical signals, and recommendation logic.
  - Should be either adapted or used as a reference, but the requested Investor Edition requires the explicit score categories and recommendation thresholds from `INVESTOR_EDITION_REQUIREMENTS.md`.

- `app/db/intelligence_persistence.py`
  - Existing psycopg2 persistence style with upsert behavior for daily report data.
  - Should be extended with fundamental and investor-ranking persistence functions to keep persistence style consistent.

- `app/db/schema_intelligence.sql`
  - Existing SQL schema file for persisted intelligence tables.
  - Should be extended with required Investor Edition tables/columns.

- `config/watchlist.yaml`
  - Existing source for core, macro, and sector symbols.
  - Should become the tracked-symbol source for Investor Edition ranking instead of adding another hardcoded list.

- `app/renderers/web_export.py`
  - Existing JSON export path for the web dashboard.
  - Should be extended to include ranked investor opportunities.

- `web/index.html`
  - Existing dashboard shell.
  - Should display ranked Investor Edition opportunities.

- `web/intelligence.html`
  - Existing full-report renderer.
  - Can optionally render a detailed Investor Edition section if `full_report.json` includes investor ranking details.

## 3. Database Changes Required

### Extend `fundamental_snapshots`

The requirements explicitly require persistence into `fundamental_snapshots` with these fields:

- `symbol`
- `snapshot_date`
- `pe_ratio`
- `roe`
- `debt_to_equity`
- `dividend_yield`
- `revenue_growth`
- `free_cash_flow`

Existing seed code already writes several `fundamental_snapshots` fields:

- `revenue`
- `net_income`
- `total_assets`
- `total_liabilities`
- `cash_and_equivalents`
- `total_debt`
- `operating_cash_flow`
- `free_cash_flow`
- `pe_ratio`
- `eps`
- `roe`
- `debt_to_equity`
- `source`

Required changes:

1. Add `dividend_yield DOUBLE PRECISION`.
2. Add `revenue_growth DOUBLE PRECISION`.
3. Ensure `UNIQUE (symbol, snapshot_date)` exists.
4. Add indexes for ranking reads:
   - `(snapshot_date)`
   - `(symbol, snapshot_date DESC)`
5. Keep existing columns and behavior to preserve backward compatibility.

### Add Investor Score Persistence

Create a new table, recommended name: `investor_scores`.

Recommended columns:

- `id SERIAL PRIMARY KEY`
- `created_at TIMESTAMP NOT NULL DEFAULT NOW()`
- `score_date DATE NOT NULL DEFAULT CURRENT_DATE`
- `symbol VARCHAR(20) NOT NULL`
- `company_name TEXT`
- `sector VARCHAR(100)`
- `buy_score DOUBLE PRECISION NOT NULL`
- `recommendation VARCHAR(50) NOT NULL`
- `valuation_score DOUBLE PRECISION`
- `dividend_score DOUBLE PRECISION`
- `financial_quality_score DOUBLE PRECISION`
- `price_position_score DOUBLE PRECISION`
- `technical_score DOUBLE PRECISION`
- `dividend_yield DOUBLE PRECISION`
- `pe_ratio DOUBLE PRECISION`
- `distance_from_52w_low DOUBLE PRECISION`
- `rsi DOUBLE PRECISION`
- `raw_score JSONB`
- `UNIQUE (score_date, symbol)`

Recommended indexes:

- `(score_date, buy_score DESC)`
- `(symbol, score_date DESC)`
- `(recommendation)`
- `(sector)`

Rationale:

- Keeps Investor Edition ranking history separate from raw fundamentals.
- Avoids overloading `technical_snapshots` or `intelligence_reports`.
- Allows dashboard reads to use one table or one exported JSON payload.

### Optional Company Profile Alignment

If `company_profiles` already exists in the live database, verify it has:

- `symbol`
- `company_name`
- `sector`
- `industry`
- `exchange`
- `market_cap`
- `updated_at`

No new table is required unless the database is missing the table outside seed scripts.

## 4. Files Requiring Modification

After plan approval, modify the following files:

- `app/collectors/fmp_fundamentals.py`
  - Add collection/normalization for `dividend_yield`.
  - Add `revenue_growth`, either from FMP growth endpoint or by comparing current and prior income statements.
  - Preserve current output keys.

- `app/db/schema_intelligence.sql`
  - Add missing `fundamental_snapshots` columns if not present.
  - Add `investor_scores`.

- `app/db/intelligence_persistence.py`
  - Add `persist_fundamental_snapshot(symbol, fundamentals)`.
  - Add `persist_investor_score(score_payload)`.
  - Add `persist_investor_scores(score_payloads)`.
  - Use upsert semantics on `(snapshot_date, symbol)` and `(score_date, symbol)`.

- `app/main.py`
  - Persist collected fundamentals during `full` mode.
  - Generate Investor Edition scores after fundamentals, profiles, quotes, and technical data are available.
  - Rank all tracked symbols by `BUY_SCORE`.
  - Include investor ranking in report output, web export, and optionally Telegram summary.
  - Preserve `degraded` and `offline` behavior.

- `app/renderers/web_export.py`
  - Accept an optional investor rankings payload.
  - Export rankings in `latest-report.json`, for example under `investor_rankings`.
  - Optionally export detailed ranking data in `full-report.json`.
  - Preserve existing JSON fields used by the current dashboard.

- `app/renderers/report.py`
  - Either expose reusable technical result generation for the Investor Edition or stop requiring Investor Edition to parse report text.
  - Avoid changing existing report behavior unless needed.

- `web/index.html`
  - Add a ranked opportunities table/cards section displaying:
    - Symbol
    - Company
    - BUY_SCORE
    - Recommendation
    - Dividend Yield
    - P/E
    - Distance From 52 Week Low
    - RSI
    - Sector
  - Keep existing market-regime, confidence, summary, bullish, bearish, and ticker sections working.

- `web/intelligence.html`
  - Optional but recommended: add a structured Investor Edition ranking section if included in `full-report.json`.

- `config/watchlist.yaml`
  - Add an `investor` group if the Investor Edition tracked universe should differ from `core`.
  - Otherwise use `core` for initial implementation.

- `README.md`
  - Document Investor Edition behavior, new persistence tables, and dashboard output after implementation.

- Test files under `app/db/` or new tests under an existing test location
  - Add focused tests for scoring thresholds, recommendation labels, persistence payload shape, and ranking order.

## 5. New Modules Required

Create the following modules after plan approval:

- `app/analytics/investor_scoring_engine.py`
  - Required by `INVESTOR_EDITION_REQUIREMENTS.md`.
  - Inputs:
    - fundamentals from FMP or `fundamental_snapshots`
    - company profile
    - quote data
    - technical indicators/signals
  - Outputs:
    - `valuation_score`
    - `dividend_score`
    - `financial_quality_score`
    - `price_position_score`
    - `technical_score`
    - `BUY_SCORE` normalized to 0-100
    - `recommendation`
    - dashboard display fields
    - raw scoring details/reasons
  - Recommendation thresholds must exactly follow requirements:
    - `BUY_SCORE >= 80`: `Strong Buy`
    - `BUY_SCORE >= 65`: `Buy`
    - `BUY_SCORE >= 50`: `Watch`
    - otherwise: `Avoid`

- `app/analytics/investor_ranking.py`
  - Loads tracked symbols from `config/watchlist.yaml`.
  - Builds per-symbol scoring inputs.
  - Calls `investor_scoring_engine.py`.
  - Sorts results by highest `BUY_SCORE`.
  - Handles missing fundamentals or technical inputs without failing the whole run.

- `app/db/investor_queries.py`
  - Optional but recommended if dashboard/export should read latest rankings from PostgreSQL.
  - Query latest rankings by `score_date`.
  - Query latest fundamentals/profile/technical records by symbol.

- `app/db/test_investor_persistence.py`
  - Lightweight persistence smoke test using sample payloads.

- `app/analytics/test_investor_scoring_engine.py`
  - Unit-level tests for score normalization and recommendation thresholds.

## 6. Recommended Implementation Order

1. Database schema preparation
   - Extend `fundamental_snapshots`.
   - Add `investor_scores`.
   - Confirm live database matches schema expectations on `db-01/alphascope`.

2. Fundamental persistence
   - Extend `collect_fundamentals()` to include `dividend_yield` and `revenue_growth`.
   - Add `persist_fundamental_snapshot()`.
   - Wire persistence into `app/main.py` for collected fundamentals.
   - Preserve existing fundamentals summary output.

3. Investor scoring engine
   - Create `app/analytics/investor_scoring_engine.py`.
   - Define deterministic category scoring for valuation, dividend, financial quality, price position, and technicals.
   - Implement exact recommendation thresholds.
   - Add unit tests for boundary scores: 80, 65, 50, and below 50.

4. Investor ranking workflow
   - Create `app/analytics/investor_ranking.py`.
   - Use `config/watchlist.yaml` `investor` group if present, else fallback to `core`.
   - Combine available FMP fundamentals, profiles, quotes, and technical indicators.
   - Sort descending by `BUY_SCORE`.

5. Investor score persistence
   - Add `persist_investor_scores()`.
   - Persist all ranked symbols with raw score details.
   - Add a smoke test with sample payloads.

6. Pipeline integration
   - Wire ranking generation and persistence into `build_full_report()`.
   - Include rankings in the returned result.
   - Keep `degraded` and `offline` modes from failing when FMP data is absent.

7. Web export integration
   - Extend `export_web_report()` to include `investor_rankings`.
   - Preserve existing `latest-report.json` and `full-report.json` fields for backward compatibility.

8. Dashboard display
   - Add a ranked opportunities section to `web/index.html`.
   - Include all required columns.
   - Add empty/error display when rankings are unavailable.

9. Full report display
   - Add an Investor Edition section to the markdown report and/or structured `full-report.json`.
   - Optionally update `web/intelligence.html` to render details directly instead of parsing text.

10. Documentation and verification
   - Update `README.md`.
   - Run targeted tests.
   - Run `python -m app.main offline` to confirm fallback still works.
   - Run full mode only when FMP, Gemini, Telegram, and PostgreSQL credentials are available.

## 7. Risks and Dependencies

- FMP field availability
  - `dividend_yield` and `revenue_growth` may not be available from the currently used endpoints.
  - Mitigation: derive `revenue_growth` from current and prior income statements if no direct field exists, and use a stable FMP ratio/profile field for dividend yield.

- Existing database schema drift
  - Seed scripts reference `market_prices`, `company_profiles`, and `fundamental_snapshots`, but `schema_intelligence.sql` currently defines only intelligence, technical, and event tables.
  - Mitigation: inspect live schema before migration and make additive, backward-compatible changes only.

- Two technical engines
  - Current daily report technicals use yfinance, while `app/analytics/technical_engine.py` uses persisted `market_prices`.
  - Mitigation: use the persisted DB-backed analytics engine for Investor Edition where possible because it already calculates 52-week low distance and richer RSI data.

- Watchlist duplication
  - `app/main.py`, `app/renderers/report.py`, seed scripts, and `config/watchlist.yaml` all define symbol lists.
  - Mitigation: use `config/watchlist.yaml` for Investor Edition and avoid changing legacy lists in the first implementation.

- Missing data for ETFs or non-dividend stocks
  - ETFs and growth stocks may have incomplete fundamentals or dividend data.
  - Mitigation: score missing inputs neutrally or conservatively, include raw reasons, and never fail the full ranking because one symbol is incomplete.

- Backward compatibility
  - Existing dashboard JavaScript expects current JSON fields.
  - Mitigation: only add new fields to web JSON; do not remove or rename existing keys.

- Mode behavior
  - `degraded` and `offline` modes intentionally disable FMP.
  - Mitigation: Investor Edition ranking should return an unavailable/empty payload in those modes unless latest persisted database data is explicitly used as a fallback.

- External services
  - Full verification depends on FMP, Gemini, Telegram, yfinance, and PostgreSQL availability.
  - Mitigation: add deterministic unit tests for scoring and payload shaping, plus separate live smoke tests for integrations.

- Recommendation semantics
  - Existing `intelligence_fusion.py` recommendation labels differ from Investor Edition requirements.
  - Mitigation: Investor Edition must implement the required `Strong Buy`, `Buy`, `Watch`, and `Avoid` labels exactly, even if existing internal labels remain unchanged elsewhere.
