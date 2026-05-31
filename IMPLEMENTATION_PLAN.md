# AlphaScope Investor Dashboard MVP Implementation Plan

Status: pending approval. This plan is the only repository change made before implementation.

## Constraints

- Preserve the static-site architecture: GitHub -> Cloudflare Pages -> public website.
- Do not add Flask, FastAPI, Django, another backend web server, or browser database access.
- Keep existing JSON exports and public pages backward compatible.
- Reuse existing dark theme, branding, layout language, and Cloudflare deployment model.
- Implement in small milestones and commit after each approved milestone.

## Current Findings

Reviewed files:

- `web/index.html`
- `web/intelligence.html`
- `app/renderers/web_export.py`
- `app/main.py`
- `app/analytics/investor_scoring_engine.py`
- `app/analytics/investor_ranking.py`
- `app/db/intelligence_persistence.py`
- `app/db/schema_intelligence.sql`

Relevant existing capabilities:

- `app/main.py` already builds `investor_rankings` and persists them through `persist_investor_scores()`.
- `investor_scores` already exists in `app/db/schema_intelligence.sql`.
- `app/renderers/web_export.py` currently exports only:
  - `web/data/latest-report.json`
  - `web/data/full-report.json`
- `web/data/full-report.json` exists locally and has the expected top-level shape:
  - `generated_at`
  - `full_report`
- `web/intelligence.html` fetches `data/full-report.json?t=...` and renders by parsing `full_report` text.
- The likely Full Market Intelligence failure is not an obvious local JSON absence. The next implementation step should verify whether Cloudflare is deploying `web/data/full-report.json`, whether the production path differs from local expectations, or whether runtime parsing fails on a specific report shape.

## Milestone 1: Fix Full Market Intelligence Page

Goal: make `web/intelligence.html` load reliably with no browser console errors.

Implementation steps:

1. Reproduce locally with a static server rooted at `web/`.
2. Verify `data/full-report.json` resolves from `intelligence.html`.
3. Check whether failures are caused by:
   - missing `web/data/full-report.json` in deployed files,
   - path mismatch,
   - malformed JSON,
   - unexpected report schema,
   - JavaScript parsing/runtime errors after a successful fetch.
4. Add defensive rendering around parsed report sections so missing sections show empty-state cards instead of breaking page execution.
5. Preserve the existing full-report text export and page URL.

Acceptance criteria:

- `web/intelligence.html` loads successfully from a local static server.
- Existing intelligence report remains accessible.
- Missing or partial report sections do not crash rendering.
- Browser console has no uncaught errors.

Commit:

- `fix web intelligence report loading`

How to test:

- Run a local static server from `web/`.
- Open `/intelligence.html`.
- Confirm the full report renders and DevTools console has no uncaught errors.

## Milestone 2: Add Investor Rankings JSON Export

Goal: generate `web/data/investor-rankings.json` from latest persisted `investor_scores`.

Implementation steps:

1. Add a small query helper, likely in `app/db/intelligence_persistence.py` or a focused `app/db/investor_queries.py`, to read the latest `score_date` from `investor_scores`.
2. Return rows ordered by `buy_score DESC`.
3. Extend `app/renderers/web_export.py` to write `web/data/investor-rankings.json`.
4. Keep `latest-report.json` and `full-report.json` unchanged except for optional additive metadata.
5. Include required fields:
   - `rank`
   - `symbol`
   - `company`
   - `buy_score`
   - `recommendation`
   - `dividend_yield`
   - `pe_ratio`
   - `roe`
   - `sector`
   - `technical_score`
   - `valuation_score`
   - `financial_quality_score`
6. Include detail-page support fields in the same payload where available:
   - `dividend_score`
   - `price_position_score`
   - `debt_to_equity`
   - `free_cash_flow`
   - `rsi`
   - `sma20`
   - `sma50`
   - `sma200`
   - `distance_from_52w_low`
   - generated strengths and risks.

Notes:

- The current `investor_scores` table does not store `roe`, `debt_to_equity`, `free_cash_flow`, `sma20`, `sma50`, or `sma200` directly. The export should join latest `fundamental_snapshots` and `technical_snapshots` where possible, or emit `null` with stable frontend formatting until the stored data is expanded.
- `investor_scores.raw_score` currently stores scoring metadata but not full explanation bullets. Explanation generation can be deterministic in export or frontend based on score fields and available metrics.

Acceptance criteria:

- `web/data/investor-rankings.json` is generated without removing existing exports.
- Rows are ranked by descending `buy_score`.
- Empty database result produces a valid JSON payload with `rankings: []`.

Commit:

- `export investor rankings json`

How to test:

- Run exporter through the existing pipeline or a targeted smoke path.
- Validate JSON with `python3 -m json.tool web/data/investor-rankings.json`.
- Confirm existing `latest-report.json` and `full-report.json` still validate.

## Milestone 3: Replace Homepage With Investor Dashboard

Goal: make the homepage answer "What should I buy and why?" with ranked opportunities first.

Implementation steps:

1. Preserve the current header, logo, ticker, dark theme, and responsive behavior.
2. Replace the hero-first layout with a compact investor dashboard layout.
3. Add Top Ranked Opportunities as the first primary section.
4. Fetch `data/investor-rankings.json` with no-store cache behavior.
5. Render required columns:
   - Rank
   - Symbol
   - Company
   - Buy Score
   - Recommendation
   - Dividend Yield
   - PE Ratio
   - ROE
   - Sector
6. Make rows sortable by Buy Score.
7. Style recommendation badges:
   - Strong Buy
   - Buy
   - Watch
   - Avoid
8. Make symbol cells link to `opportunity.html?symbol=SYMBOL`.
9. Move existing Market Regime, Confidence, Executive Summary, bullish list, bearish list, and intelligence-report link below Top Ranked Opportunities.
10. Preserve fallbacks for missing JSON or empty rankings.

Acceptance criteria:

- Homepage prioritizes Top Ranked Opportunities.
- Buy Score sorting works.
- Market context still loads from `latest-report.json`.
- Existing Full Intelligence link remains accessible.
- Mobile layout does not overflow.

Commit:

- `add investor dashboard homepage`

How to test:

- Serve `web/` locally.
- Open `/`.
- Confirm rankings load, sort works, links navigate, and market context still renders.

## Milestone 4: Create Opportunity Detail Page

Goal: add `web/opportunity.html` for symbol-level investment explanations.

Implementation steps:

1. Create `web/opportunity.html` using the same visual design language as existing pages.
2. Read `symbol` from the query string.
3. Fetch `data/investor-rankings.json`.
4. Locate the selected symbol case-insensitively.
5. Display required sections:
   - Summary: Symbol, Company, Buy Score, Recommendation
   - Score Breakdown: Valuation, Dividend, Financial Quality, Technical, Price Position
   - Fundamentals: PE Ratio, ROE, Debt-to-Equity, Dividend Yield, Free Cash Flow
   - Technicals: RSI, SMA20, SMA50, SMA200, Distance from 52 Week Low
   - Why This Is Ranked Here: Strengths and Risks
6. If symbol is missing or unknown, show a clear static error state with a link back to `/`.
7. Generate explanation bullets deterministically from the available metrics and score bands if not present in JSON.

Acceptance criteria:

- `opportunity.html?symbol=MSFT` renders a useful detail view when MSFT exists in rankings.
- Unknown symbols do not crash.
- No backend or browser database access is introduced.

Commit:

- `add opportunity detail page`

How to test:

- Open `/opportunity.html?symbol=MSFT`.
- Open `/opportunity.html?symbol=UNKNOWN`.
- Confirm console has no uncaught errors.

## Milestone 5: Implement Automatic Refresh Architecture

Goal: refresh AlphaScope three times daily and redeploy the static site through the existing GitHub -> Cloudflare Pages path.

Recommended approach:

- Use cron on `automation-01` for the initial automated refresh.
- Schedule at `09:00`, `13:00`, and `17:00` in `America/Toronto`.
- Run the existing Python pipeline.
- Commit regenerated static JSON and report artifacts back to the branch Cloudflare Pages watches.
- Let Cloudflare Pages auto-deploy on push.

Why `automation-01` cron is the initial MVP:

- It fits the current GitHub -> Cloudflare Pages deployment model.
- It keeps database/API credentials on the automation host instead of moving them into GitHub secrets immediately.
- It allows the existing operational environment to run the same pipeline used manually today.
- It keeps generated static assets auditable in git.
- It can be replaced by GitHub Actions later because the dashboard only consumes static JSON files.

Workflow design:

1. Cron on `automation-01` starts the refresh shell script at the scheduled Toronto times.
2. The script changes into the AlphaScope repository.
3. The script loads the local Python environment and required environment variables.
4. The script runs AlphaScope, for example `python -m app.main full`.
5. The pipeline updates PostgreSQL, reports, and web JSON exports.
6. The script validates generated JSON:
   - `web/data/latest-report.json`
   - `web/data/full-report.json`
   - `web/data/investor-rankings.json`
7. The script commits only changed generated web artifacts:
   - `web/data/latest-report.json`
   - `web/data/full-report.json`
   - `web/data/investor-rankings.json`
   - optionally latest `reports/*.md` if the project intentionally tracks generated reports.
8. The script pushes to the deployment branch on GitHub.
9. Cloudflare Pages redeploys automatically from the GitHub push.
10. The script logs start time, end time, exit status, commit SHA when applicable, and success/failure summary.

Dedicated shell script:

- Add `scripts/refresh_alphascope.sh`.
- Responsibilities:
  - use strict shell settings,
  - acquire a lock so overlapping runs cannot corrupt generated artifacts,
  - write all output to a persistent log file,
  - run the AlphaScope pipeline,
  - validate JSON exports,
  - commit generated web artifacts only when files changed,
  - push to GitHub,
  - emit clear success/failure status.
- Recommended log path on `automation-01`:
  - `logs/automation-refresh.log` inside the repository, or
  - `/var/log/alphascope/automation-refresh.log` if permissions and log rotation are configured.
- The script should be scheduler-neutral: cron and future GitHub Actions should both be able to call the same workflow or an equivalent command path without frontend changes.

Cron design:

- Install crontab on `automation-01` using the server timezone set to `America/Toronto`, or explicitly set `CRON_TZ=America/Toronto` in the crontab.
- Initial cron entries:
  - `CRON_TZ=America/Toronto`
  - `0 9 * * * /home/dmudalige/projects/alphascope/scripts/refresh_alphascope.sh`
  - `0 13 * * * /home/dmudalige/projects/alphascope/scripts/refresh_alphascope.sh`
  - `0 17 * * * /home/dmudalige/projects/alphascope/scripts/refresh_alphascope.sh`
- If the deployment path on `automation-01` differs from the local development path, document the production path in the automation setup notes instead of hardcoding assumptions into the frontend.

Files to add or update:

- `scripts/refresh_alphascope.sh`
- README or implementation notes documenting:
  - `automation-01` cron schedule,
  - timezone handling with `America/Toronto`,
  - required local environment variables and credentials,
  - deployment branch,
  - generated files,
  - log file path,
  - how to modify the schedule,
  - how to run manually,
  - how to disable automation,
  - how to troubleshoot failures.

GitHub Actions future replacement:

- Keep the dashboard frontend dependent only on static JSON files under `web/data/`.
- Keep the generated JSON schema stable.
- Keep the refresh workflow as a repository script so a later GitHub Actions workflow can call the same script or equivalent commands.
- A later GitHub Actions migration should only replace the scheduler/execution host, not `web/index.html`, `web/intelligence.html`, or `web/opportunity.html`.

Acceptance criteria:

- `scripts/refresh_alphascope.sh` exists and can be run manually on `automation-01`.
- Cron runs are scheduled for `09:00`, `13:00`, and `17:00` `America/Toronto`.
- Each run logs start, success/failure, and enough detail to troubleshoot failures.
- Successful refresh updates database, regenerates JSON, pushes static assets, and triggers Cloudflare Pages.
- JSON validation failure prevents commit/push and is logged as a failed run.
- Preview deployments and branch previews remain normal Cloudflare Pages behavior.
- Future GitHub Actions replacement does not require dashboard frontend changes.

Commit:

- `add scheduled investor dashboard refresh`

How to test:

- Run `scripts/refresh_alphascope.sh` manually on `automation-01`.
- Confirm generated JSON validates.
- Confirm GitHub push triggers Cloudflare Pages deployment.
- Confirm production page shows fresh `generated_at` and rankings.
- Confirm log file records success.
- Temporarily run with an intentional JSON validation failure in a safe test branch or dry-run mode and confirm failure is logged without pushing.

## Final Verification

After all milestones:

- Validate all generated JSON files with `python3 -m json.tool`.
- Serve `web/` locally and test:
  - `/`
  - `/intelligence.html`
  - `/opportunity.html?symbol=MSFT`
- Check browser console on each page.
- Run focused Python tests for scoring/persistence/export helpers if present.
- Confirm `git status` contains only intended changes before each milestone commit.

## Approval Needed

Implementation should begin only after this plan is approved.
