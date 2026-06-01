# AlphaScope Investor Edition Sprint 1 Implementation Plan

Status: pending approval. No application code changes should be made until this plan is approved.

## Sprint Objective

Transform AlphaScope from a report-centric interface into an investor-centric dashboard while preserving the existing backend architecture, PostgreSQL persistence, static web deployment through Cloudflare Pages, automation pipeline, and AlphaScope branding.

## Non-Goals And Constraints

- Do not introduce new collectors.
- Do not introduce new AI providers.
- Do not add portfolio tracking, broker integrations, trading workflows, or account-level features.
- Do not replace PostgreSQL persistence, the current Python pipeline, static web export model, Telegram delivery, or existing Cloudflare Pages deployment.
- Preserve existing JSON exports and the detailed intelligence experience.
- Prefer additive, backward-compatible changes.

## Current Findings

Relevant existing implementation:

- `app/main.py` already orchestrates the AlphaScope run, persists fundamentals, builds investor rankings, exports web JSON, and sends Telegram.
- `app/config/symbols.py` currently limits the core investor universe to 7 symbols: `AAPL`, `MSFT`, `NVDA`, `AMZN`, `META`, `GOOGL`, `TSLA`.
- `config/watchlist.yaml` currently has only `core`, `macro`, and `sectors`; `app/analytics/investor_ranking.py` supports an `investor` group but falls back to `core` because the group is absent.
- Existing FMP collectors already support quotes, profiles, and fundamentals on arbitrary symbol lists, so Sprint 1 can expand the symbol set without adding collectors.
- `app/analytics/investor_scoring_engine.py` already calculates valuation, dividend, financial quality, price position, technical score, composite buy score, and recommendation.
- `app/db/intelligence_persistence.py` already persists `fundamental_snapshots`, `investor_scores`, and fetches latest investor rankings with joined fundamentals and technicals.
- `app/renderers/web_export.py` already emits `web/data/latest-report.json`, `web/data/full-report.json`, and `web/data/investor-rankings.json`.
- `web/index.html` already shows an investor ranking table, but it needs Sprint 1 UX additions and homepage reprioritization.
- `web/opportunity.html` already exists as a symbol detail page.
- `web/intelligence.html` already exists and can become the separate Analyst Dashboard destination.
- `requirements.txt` includes `pandas`; Excel export can likely use `pandas.DataFrame.to_excel`, but the implementation must verify whether an Excel writer dependency is available in the runtime. If not, add the smallest compatible dependency such as `openpyxl`.

## Target Investor Universe

Add an approximately 50-symbol investor universe using existing FMP quote/profile/fundamental collection and existing technical/database scoring paths.

Proposed initial universe:

```text
AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA,
AVGO, ORCL, CRM, ADBE, AMD, CSCO, IBM, QCOM, TXN, INTC,
JPM, BAC, WFC, GS, MS, V, MA, AXP,
UNH, JNJ, LLY, MRK, ABBV, PFE, TMO, ABT,
XOM, CVX, COP,
PG, KO, PEP, COST, WMT, HD, MCD, NKE,
CAT, HON, GE, RTX,
NEE, SO, DUK,
O, AMT
```

This gives broad sector coverage and includes dividend-oriented names without changing the collector architecture. Final list can be adjusted during implementation if a symbol is unsupported by existing data sources.

## Data Contract Changes

### `web/data/investor-rankings.json`

Keep the existing payload backward compatible and ensure each row includes:

- `rank`
- `symbol`
- `company`
- `sector`
- `current_price`
- `dividend_yield`
- `buy_score`
- `recommendation`
- `valuation_score`
- `dividend_score`
- `financial_quality_score`
- `price_position_score`
- `technical_score`
- `pe_ratio`
- `roe`
- `debt_to_equity`
- `free_cash_flow`
- `rsi`
- `sma20`
- `sma50`
- `sma200`
- `distance_from_52w_low`
- deterministic `strengths`, `risks`, and `missing_data` explanation fields where feasible.

Current price should come from the same existing FMP quote payload used during the run or from latest persisted market price data if available. Do not add a new data source.

### `web/data/latest-report.json`

Keep existing fields and add an optional `top_opportunities` array with the top-ranked investor rows needed for dashboard summary cards and Telegram parity.

### `web/data/investor-rankings.xlsx`

Generate on every successful AlphaScope run alongside the JSON exports. Include at minimum:

- Rank
- Symbol
- Company
- Sector
- Current Price
- Dividend Yield
- Buy Score
- Recommendation
- Valuation Score
- Dividend Score
- Financial Quality Score
- Price Position Score
- Technical Score
- PE Ratio
- ROE
- Distance From 52 Week Low
- RSI
- Generated At

## Milestone 1: Expand Investor Universe

Goal: move from the current 7-symbol investor set to an approximately 50-symbol universe using existing collectors and scoring.

Implementation steps:

1. Add an explicit `investor` group to `config/watchlist.yaml`.
2. Update `app/config/symbols.py` so `CORE_SYMBOLS`, `FMP_WATCHLIST`, and `FUNDAMENTAL_SYMBOLS` align with the expanded universe without breaking existing imports.
3. Keep macro and sector lists unchanged.
4. Ensure `build_investor_rankings()` uses the expanded investor universe by default.
5. Review tests that assume the old 7-symbol universe and update them to assert coverage rather than exact old membership.

Acceptance criteria:

- Investor rankings are generated for approximately 50 symbols when data is available.
- Existing FMP quote/profile/fundamental collectors are reused.
- No new collectors or providers are introduced.
- Existing 7 core symbols remain included.

## Milestone 2: Enrich Ranking Data And Explanations

Goal: ensure rankings expose the fields needed by the investor dashboard and explanation UX.

Implementation steps:

1. Carry current price through `score_investor_opportunity()` or enrich rows during export from existing quote/persistence data.
2. Extend `web_export.py` row formatting to include `current_price`, `missing_data`, and stable score explanation inputs.
3. Keep scoring weights and recommendation thresholds backward compatible unless a defect is found.
4. Add deterministic explanation generation:
   - valuation contribution
   - dividend contribution
   - financial quality contribution
   - technical contribution
   - price position contribution
   - missing-data caveats
5. Update focused tests for ranking export shape.

Acceptance criteria:

- Every ranking row has company name, sector, current price, dividend yield, buy score, and recommendation.
- Missing fields render as `null` in JSON and `--` in the UI, not as crashes.
- Explanation fields are deterministic and require no new AI call.

## Milestone 3: Generate Excel Rankings Export

Goal: create `web/data/investor-rankings.xlsx` during every AlphaScope run.

Implementation steps:

1. Add an Excel export function near the existing web export code.
2. Use the same normalized ranking rows as JSON to avoid divergent business logic.
3. Verify runtime Excel writer support.
4. Add `openpyxl` only if required by the installed pandas environment.
5. Update `scripts/alphascope_refresh.sh` validation to check that the XLSX file exists and is non-empty.

Acceptance criteria:

- `web/data/investor-rankings.xlsx` is generated every run.
- JSON exports remain unchanged except for additive fields.
- Automation validation fails clearly if the XLSX export is missing or empty.

## Milestone 4: Redesign Homepage Around Investor Decisions

Goal: make `web/index.html` prioritize Market Snapshot and Investor Rankings.

Implementation steps:

1. Replace the marketing-style hero emphasis with a compact operational dashboard first screen.
2. Put Market Snapshot at the top:
   - market regime
   - confidence
   - last update
   - concise summary
3. Put Investor Rankings immediately after or beside Market Snapshot depending on responsive layout.
4. Keep the required columns:
   - Company
   - Sector
   - Current Price
   - Dividend Yield
   - Buy Score
   - Recommendation
5. Add a Buy Score tooltip explaining the score components and weights.
6. Add a score breakdown modal triggered from each row.
7. Preserve the ticker, brand styling, mobile layout, and existing data fetch approach.
8. Add a prominent navigation link to the Analyst Dashboard page.

Acceptance criteria:

- First viewport answers market context and top investor opportunities.
- Tooltip explains Buy Score without requiring a detail-page click.
- Score breakdown modal shows the five component scores and explanation bullets.
- Table remains usable on mobile without horizontal clipping beyond the intended table scroll.

## Milestone 5: Separate Analyst Dashboard Experience

Goal: move the detailed intelligence/report-centric experience into a distinct Analyst Dashboard page.

Implementation steps:

1. Keep `web/intelligence.html` available and label it as Analyst Dashboard.
2. Ensure homepage links to Analyst Dashboard instead of treating full intelligence as the primary experience.
3. Preserve existing full-report loading and defensive rendering.
4. Avoid deleting existing report data or changing report generation semantics.

Acceptance criteria:

- Investor dashboard is the homepage.
- Analyst Dashboard remains accessible from the homepage.
- Existing detailed intelligence report still loads from static JSON.

## Milestone 6: Telegram Top Opportunities

Goal: extend the existing Telegram summary with Top Opportunities.

Implementation steps:

1. Pass `investor_rankings` from `build_full_report()` into `build_telegram_summary()`.
2. Add a concise `TOP OPPORTUNITIES` section with the top 5 ranked names.
3. Include symbol, company if concise, buy score, recommendation, and dividend yield.
4. Keep Telegram message length under the existing `TELEGRAM_MAX_MESSAGE` behavior.
5. Preserve all existing Telegram sections.

Acceptance criteria:

- Telegram summary includes Top Opportunities on successful full runs.
- Existing summary sections remain present.
- Missing rankings produce a short fallback line rather than failing delivery.

## Milestone 7: Verification And Regression Coverage

Recommended checks:

```bash
python -m unittest app.analytics.test_investor_scoring_engine
python -m unittest app.renderers.test_web_export
python -m unittest app.test_investor_symbol_coverage
python3 -m json.tool web/data/latest-report.json
python3 -m json.tool web/data/investor-rankings.json
python3 -m json.tool web/data/full-report.json
```

Additional manual checks:

- Serve `web/` locally and open `/`.
- Confirm Market Snapshot and Investor Rankings dominate the homepage.
- Confirm Buy Score tooltip appears.
- Confirm score breakdown modal opens, closes, and handles missing values.
- Confirm `/intelligence.html` still loads as Analyst Dashboard.
- Confirm `/opportunity.html?symbol=MSFT` still works.
- Confirm `web/data/investor-rankings.xlsx` opens and contains the same ranked universe as JSON.

## Implementation Order

1. Expand configuration and symbol coverage.
2. Enrich ranking/export fields.
3. Add XLSX export.
4. Update Telegram summary.
5. Redesign homepage and explanation UX.
6. Preserve and relabel Analyst Dashboard.
7. Run focused tests and static web smoke checks.

## Approval Gate

Implementation should begin only after this plan is approved.
