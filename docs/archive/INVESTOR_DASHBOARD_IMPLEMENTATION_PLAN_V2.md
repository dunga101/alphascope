# AlphaScope Investor Dashboard Implementation Plan V2

## Objective

Replace the existing static web UI with an Investor Edition dashboard while preserving AlphaScope's current static-site architecture.

The new dashboard should consume structured JSON exported by `app/renderers/web_export.py` instead of parsing report prose. The existing intelligence report can remain available as raw text, but it should no longer be the primary data source for UI rendering.

## 1. Proposed File Structure

Recommended static web structure:

```text
web/
  index.html
  opportunity.html
  intelligence.html
  assets/
    css/
      base.css
      dashboard.css
      opportunity.css
      intelligence.css
    js/
      api.js
      formatters.js
      dashboard.js
      opportunity.js
      intelligence.js
    img/
      logo.svg
  data/
    latest-report.json
    investor-rankings.json
    opportunities/
      AAPL.json
      MSFT.json
      ...
    full-report.json
  legacy/
    index.previous.html
    intelligence.previous.html
```

Recommended page responsibilities:

- `index.html`
  - Investor Edition dashboard home.
  - Shows market context and ranked opportunities.

- `opportunity.html`
  - Single-symbol opportunity detail page.
  - Reads symbol from query string, for example `opportunity.html?symbol=AAPL`.

- `intelligence.html`
  - Structured full intelligence report.
  - Keeps raw report text as appendix/fallback.

- `assets/js/api.js`
  - Fetch helpers for static JSON.
  - Handles cache-busting, error states, and fallback data.

- `assets/js/formatters.js`
  - Number, percentage, currency, score, date, and recommendation formatting.

- `assets/js/dashboard.js`
  - Dashboard-specific rendering.

- `assets/js/opportunity.js`
  - Detail-page rendering.

- `assets/js/intelligence.js`
  - Full report rendering.

- `assets/css/base.css`
  - Shared typography, colors, layout utilities, tables, status pills, cards, buttons.

## 2. JSON Contract Required From `web_export.py`

The web layer should receive structured data. It should not parse prose sections from `full_report`.

### `web/data/latest-report.json`

Purpose: lightweight dashboard bootstrap payload.

Required shape:

```json
{
  "schema_version": "2.0",
  "generated_at": "2026-05-31 15:30 EDT",
  "mode": "FULL",
  "market": {
    "regime": "RISK_ON",
    "confidence": 74,
    "summary": "Short summary text",
    "risk_flags": [],
    "bullish": [],
    "bearish": []
  },
  "ticker": [
    {
      "symbol": "AAPL",
      "price": 201.45,
      "change_pct": 1.23
    }
  ],
  "top_opportunities": [
    {
      "symbol": "MSFT",
      "company": "Microsoft Corporation",
      "buy_score": 72.75,
      "recommendation": "Buy",
      "dividend_yield": 0.00790689,
      "pe_ratio": 26.7017,
      "distance_from_52w_low": 43.2,
      "rsi": 58.4,
      "sector": "Technology"
    }
  ]
}
```

### `web/data/investor-rankings.json`

Purpose: full ranked opportunities list.

Required shape:

```json
{
  "schema_version": "2.0",
  "generated_at": "2026-05-31 15:30 EDT",
  "rankings": [
    {
      "rank": 1,
      "symbol": "MSFT",
      "company": "Microsoft Corporation",
      "sector": "Technology",
      "buy_score": 72.75,
      "recommendation": "Buy",
      "valuation_score": 60,
      "dividend_score": 50,
      "financial_quality_score": 88,
      "price_position_score": 75,
      "technical_score": 65,
      "dividend_yield": 0.00790689,
      "pe_ratio": 26.7017,
      "distance_from_52w_low": 43.2,
      "rsi": 58.4,
      "raw_score": {
        "fundamentals_available": true,
        "technical_available": true,
        "weights": {
          "valuation": 0.25,
          "dividend": 0.15,
          "financial_quality": 0.30,
          "price_position": 0.15,
          "technical": 0.15
        }
      }
    }
  ]
}
```

### `web/data/opportunities/{SYMBOL}.json`

Purpose: single-symbol detail page.

Required shape:

```json
{
  "schema_version": "2.0",
  "generated_at": "2026-05-31 15:30 EDT",
  "symbol": "MSFT",
  "company": "Microsoft Corporation",
  "sector": "Technology",
  "recommendation": "Buy",
  "buy_score": 72.75,
  "scores": {
    "valuation": 60,
    "dividend": 50,
    "financial_quality": 88,
    "price_position": 75,
    "technical": 65
  },
  "fundamentals": {
    "pe_ratio": 26.7017,
    "roe": 0.2965,
    "debt_to_equity": 0.1375,
    "dividend_yield": 0.00790689,
    "free_cash_flow": 71611000000,
    "revenue": 281724000000,
    "net_income": 101832000000
  },
  "technical": {
    "price": 510.15,
    "rsi": 58.4,
    "distance_from_52w_low": 43.2,
    "sma20": 502.1,
    "sma50": 488.4,
    "sma200": 430.7
  },
  "profile": {
    "industry": "Software",
    "market_cap": 3790000000000,
    "beta": 0.9,
    "exchange": "NASDAQ"
  },
  "explanation": {
    "strengths": [],
    "risks": [],
    "missing_data": []
  }
}
```

### `web/data/full-report.json`

Purpose: structured intelligence report plus raw text fallback.

Required shape:

```json
{
  "schema_version": "2.0",
  "generated_at": "2026-05-31 15:30 EDT",
  "sections": {
    "unified_market_regime": {},
    "event_intelligence": {},
    "market_intelligence": {},
    "earnings_context": {},
    "technical_appendix": []
  },
  "raw_report": "Original markdown/text report"
}
```

Backward compatibility:

- Keep the old `full_report` key during migration.
- New UI should use `sections` and only display `raw_report` as fallback.

## 3. Dashboard Page Layout

`index.html` should become the primary Investor Edition dashboard.

### Header

- Brand: AlphaScope Investor Edition.
- Last updated timestamp.
- System mode badge: `FULL`, `DEGRADED`, or `OFFLINE`.
- Link to full intelligence report.

### Market Context Band

Compact top band with:

- Market regime.
- Confidence.
- Executive summary.
- Risk flags.

This is context, not the main page focus.

### Opportunity Ranking Table

Main dashboard component.

Columns:

- Rank
- Symbol
- Company
- BUY_SCORE
- Recommendation
- Dividend Yield
- P/E
- Distance From 52 Week Low
- RSI
- Sector

Behavior:

- Default sort by `BUY_SCORE` descending.
- Row click opens `opportunity.html?symbol=SYMBOL`.
- Recommendation pill styling:
  - Strong Buy
  - Buy
  - Watch
  - Avoid
- Missing values display as `--`, not `null`.

### Score Distribution Summary

Small summary cards:

- Number of Strong Buy candidates.
- Number of Buy candidates.
- Average BUY_SCORE.
- Highest dividend yield.
- Lowest P/E.

### Ticker Strip

Keep a compact ticker strip, but make it secondary.

### Empty/Error States

Required states:

- JSON fetch failed.
- Rankings unavailable.
- Generated payload has unsupported schema version.
- No opportunities found.

## 4. Opportunity Detail Page Layout

`opportunity.html` should render one symbol using `web/data/opportunities/{SYMBOL}.json`.

### Header

- Symbol.
- Company name.
- Sector.
- Recommendation pill.
- BUY_SCORE.
- Back to dashboard link.

### Score Breakdown

Cards or horizontal bars:

- Valuation Score
- Dividend Score
- Financial Quality Score
- Price Position Score
- Technical Score

Each should show:

- Score value.
- Short explanation.
- Whether data was complete.

### Fundamentals Panel

Metrics:

- P/E
- ROE
- Debt-to-equity
- Dividend yield
- Free cash flow
- Revenue
- Net income

### Price Position Panel

Metrics:

- Current price
- Distance from 52-week low
- RSI
- SMA20
- SMA50
- SMA200

### Explanation Panel

Structured lists:

- Why this ranks where it does.
- Key strengths.
- Key risks.
- Missing data.

### Raw Data Appendix

Collapsible JSON payload for debugging and auditability.

## 5. Chart Requirements

Use lightweight static-friendly charts. Avoid heavy frameworks initially.

MVP chart options:

- CSS bars for score breakdown.
- Small inline SVG or canvas for score distribution.
- No external CDN dependency required.

Required MVP charts:

1. BUY_SCORE bar in ranking table.
2. Opportunity detail score breakdown bars.
3. Dashboard recommendation distribution:
   - Strong Buy
   - Buy
   - Watch
   - Avoid

Future chart candidates:

- Historical BUY_SCORE trend by symbol.
- Dividend yield comparison.
- P/E comparison by sector.
- Price distance from 52-week low scatter plot.
- Technical RSI band chart.

Chart data should come from JSON, not DOM parsing.

## 6. Mobile Responsiveness Strategy

Target behavior:

- Desktop: full table and multi-column cards.
- Tablet: compressed table with horizontal scroll.
- Mobile: card-based opportunity list instead of full table.

Approach:

- Use CSS grid and container-width breakpoints.
- Keep desktop ranking table for screens above `900px`.
- On screens below `760px`, render each opportunity as a card with:
  - Symbol/company
  - BUY_SCORE
  - Recommendation
  - Dividend yield
  - P/E
  - Sector
- Avoid fixed pixel widths in tables except for numeric columns.
- Use `overflow-x: auto` only as fallback.
- Touch targets at least `44px` high.
- Keep first viewport useful: header, market context, and first ranked candidates should be visible quickly.

Accessibility:

- Semantic tables for desktop.
- Buttons/links with visible focus states.
- ARIA live region for data load status.
- Color should not be the only signal for recommendation.

## 7. Migration Plan From Existing `web/` Folder

### Step 1: Preserve Legacy Files

Before replacement:

```text
web/legacy/index.previous.html
web/legacy/intelligence.previous.html
```

Move current files there for reference.

### Step 2: Add Shared Assets

Create:

```text
web/assets/css/
web/assets/js/
web/assets/img/
```

Move shared styling and rendering utilities out of inline page scripts.

### Step 3: Extend `web_export.py`

Add structured JSON exports:

- `latest-report.json`
- `investor-rankings.json`
- `opportunities/{SYMBOL}.json`
- `full-report.json`

Keep old keys temporarily:

- `ticker`
- `regime`
- `confidence`
- `summary`
- `full_report`

### Step 4: Replace Dashboard

Replace `web/index.html` with the Investor Edition dashboard.

Acceptance criteria:

- Loads `latest-report.json`.
- Loads `investor-rankings.json`.
- Displays ranked opportunities.
- Handles empty/error states.

### Step 5: Replace Intelligence Page

Replace `web/intelligence.html` with a structured renderer.

Acceptance criteria:

- Uses `sections` from `full-report.json`.
- Displays raw report fallback.
- Does not parse section text for primary UI.

### Step 6: Add Opportunity Detail Page

Create `web/opportunity.html`.

Acceptance criteria:

- Opens from dashboard row click.
- Loads `web/data/opportunities/{SYMBOL}.json`.
- Shows score breakdown and fundamentals.

### Step 7: Validation

Validate with:

- Fresh generated JSON.
- Missing JSON files.
- Empty rankings.
- Mobile viewport.
- Desktop viewport.
- Browser console free of runtime errors.

## 8. Minimum Viable Dashboard (MVP)

MVP scope should be intentionally narrow.

Required MVP:

1. Replace `index.html`.
2. Extend `web_export.py` to write `investor-rankings.json`.
3. Render ranked opportunities table.
4. Show market regime/confidence/summary.
5. Add recommendation pills.
6. Add mobile card view.
7. Add error/empty states.
8. Preserve link to `intelligence.html`.

MVP does not require:

- Historical charts.
- Sector filters.
- Search.
- User preferences.
- Authentication.
- External charting libraries.
- Brokerage integrations.

MVP acceptance criteria:

- Dashboard loads from static files only.
- No JavaScript errors.
- Ranking data is visible within first viewport on desktop.
- Mobile layout is readable.
- Existing AlphaScope pipeline still completes if web export succeeds.

## 9. Future Enhancement Phases

### Phase 2.1: Structured Detail Pages

- Add `opportunity.html`.
- Export per-symbol opportunity JSON.
- Add score breakdown bars.
- Add fundamentals and technical panels.

### Phase 2.2: Structured Intelligence Report

- Replace prose parsing in `intelligence.html`.
- Add structured report sections to `full-report.json`.
- Keep raw report appendix.

### Phase 2.3: Filtering and Sorting

- Sort by BUY_SCORE, dividend yield, P/E, RSI, sector.
- Filter by recommendation.
- Filter by sector.
- Search symbol/company.

### Phase 2.4: Historical Investor Scores

Requires database and export support.

- Export recent `investor_scores` history.
- Show BUY_SCORE trend.
- Show recommendation changes over time.
- Highlight new entrants and upgrades/downgrades.

### Phase 2.5: Dividend-Focused Views

- Dedicated dividend opportunity view.
- Sort by dividend yield.
- Show payout ratio if available.
- Show dividend coverage from free cash flow.
- Add warnings for unusually high yield.

### Phase 2.6: Sector and Portfolio Context

- Sector score averages.
- Sector opportunity heatmap.
- Watchlist grouping.
- User-defined core/dividend/growth groups in config.

### Phase 2.7: Operational Hardening

- JSON schema version checks.
- Payload validation in `web_export.py`.
- Browser-side telemetry or error file.
- Static smoke test using Playwright.
- Screenshot regression checks for desktop and mobile.

## Recommended Development Order

1. Update `web_export.py` JSON contract.
2. Build `assets/js/api.js` and `assets/js/formatters.js`.
3. Replace `index.html` with MVP dashboard.
4. Validate desktop/mobile dashboard.
5. Add `opportunity.html`.
6. Replace `intelligence.html` prose parser.
7. Add charts and filters.

## Review Questions Before Development

1. Should the dashboard default to all `core` symbols or only symbols with complete fundamentals?
2. Should ETFs like `SPY` appear in Investor Edition rankings or only in market context?
3. Should `Avoid` symbols be visible by default or collapsed?
4. Should dividend yield be shown as raw decimal or percent?
5. Should historical score export be added now or deferred?
