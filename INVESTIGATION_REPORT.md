# AlphaScope Fundamental Data Investigation Report

Generated: 2026-06-04

## Executive Summary

Root cause: affected symbols are not receiving persisted fundamental snapshots because the configured FMP plan/API response returns HTTP 402 Payment Required for their fundamental endpoints. The collector returns `status: ERROR`, `collect_fmp_layer()` drops those symbols from the in-memory `fundamentals` map, and `build_investor_rankings()` still scores every investor universe symbol. Missing fundamentals trigger deterministic default component scores, producing the identical `47.25` `Avoid` score pattern.

Confidence level: HIGH.

Impact:

- Affected symbols: `AVGO`, `ORCL`, `IBM`, `MA`, `LLY`, `MRK`, `PG`.
- User-facing PE Ratio, ROE, and Dividend Yield appear as `0` / `0%` because dashboard formatters call `Number(null)`, which evaluates to `0`.
- Persisted and exported data contain `NULL`/`null`, not actual zero, for these affected metrics.
- Investor recommendations are materially unreliable for symbols with missing fundamentals because the scoring engine treats missing data as neutral/default component scores rather than excluding, flagging, or heavily penalizing incomplete records.

Affected components:

- FMP collection: `app/collectors/fmp_fundamentals.py`
- Investor ranking orchestration: `app/analytics/investor_ranking.py`
- Scoring defaults: `app/analytics/investor_scoring_engine.py`
- Persistence/export: `app/db/intelligence_persistence.py`, `app/renderers/web_export.py`
- Dashboard rendering: `web/index.html`, `web/opportunity.html`

## Architecture Trace

AVGO flow:

```text
FMP API
  stable/income-statement?symbol=AVGO
  stable/balance-sheet-statement?symbol=AVGO
  stable/cash-flow-statement?symbol=AVGO
  stable/ratios-ttm?symbol=AVGO
    |
    v
app/collectors/fmp_fundamentals.py
  collect_fundamentals("AVGO")
  r.raise_for_status() raises HTTP 402
  returns {"status": "ERROR", "symbol": "AVGO", "reason": "...Payment Required..."}
    |
    v
app/main.py
  collect_fmp_layer()
  only keeps f when f["status"] == "OK"
  AVGO is dropped from fundamentals dict
    |
    v
app/analytics/investor_ranking.py
  build_investor_rankings()
  still iterates all investor symbols from config/watchlist.yaml
  passes fundamentals.get("AVGO") -> None
    |
    v
app/analytics/investor_scoring_engine.py
  score_investor_opportunity()
  fundamentals = fundamentals or {}
  PE, ROE, dividend_yield become None
  default component scores:
    valuation=45, dividend=40, financial_quality=50,
    price_position=50, technical=50
  buy_score = 47.25, recommendation = Avoid
    |
    v
app/db/intelligence_persistence.py
  persist_investor_score()
  stores investor_scores row with pe_ratio NULL, dividend_yield NULL,
  raw_score.fundamentals_available=false
  no fundamental_snapshots row exists for AVGO
    |
    v
app/renderers/web_export.py
  fetch_latest_investor_rankings()
  left-joins latest fundamental_snapshots for ROE/debt/FCF
  _format_investor_row() exports nulls to web/data/investor-rankings.json
    |
    v
web/index.html / web/opportunity.html
  formatNumber(null) and formatPercent(null) use Number(null)
  browser displays 0 / 0%
```

## Findings

### Finding 1: FMP returns HTTP 402 for affected symbol fundamentals

Evidence from live collector run:

| Symbol | Collector status | Reason |
|---|---:|---|
| AVGO | ERROR | `402 Client Error: Payment Required` on `stable/income-statement` |
| ORCL | ERROR | `402 Client Error: Payment Required` on `stable/income-statement` |
| IBM | ERROR | `402 Client Error: Payment Required` on `stable/income-statement` |
| MA | ERROR | `402 Client Error: Payment Required` on `stable/income-statement` |
| LLY | ERROR | `402 Client Error: Payment Required` on `stable/income-statement` |
| MRK | ERROR | `402 Client Error: Payment Required` on `stable/income-statement` |
| PG | ERROR | `402 Client Error: Payment Required` on `stable/income-statement` |
| AAPL | OK | cache hit with PE, ROE, dividend yield, debt-to-equity, FCF |

Raw FMP response example for AVGO ratios/income/balance/cashflow:

```text
Premium Query Parameter: 'Special Endpoint : This value set for 'symbol' is not available under your current subscription please visit our subscription page to upgrade your plan at https://financialmodelingprep.com/
```

Control check: AAPL `stable/ratios-ttm` returns a normal JSON array containing fields such as `priceToEarningsRatioTTM`, `debtToEquityRatioTTM`, and `dividendYieldTTM`.

Relevant code:

- `app/collectors/fmp_fundamentals.py:74` `collect_fundamentals()`
- `app/collectors/fmp_fundamentals.py:98` calls `r.raise_for_status()`
- `app/collectors/fmp_fundamentals.py:143` catches exceptions and returns `status: ERROR`

Conclusion: FMP is not returning usable fundamental JSON for the affected symbols under the current subscription/API behavior.

### Finding 2: Affected fundamentals are dropped before persistence

`app/main.py` keeps only successful collector payloads:

```python
for symbol in FUNDAMENTAL_SYMBOLS:
    f = collect_fundamentals(symbol)

    if f.get("status") == "OK":
        fundamentals[symbol] = f
```

Because affected symbols return `ERROR`, they are absent from the `fundamentals` dict. `persist_fundamental_results()` only persists entries in that dict, so no `fundamental_snapshots` row is written for those symbols.

Database verification:

| Group | Symbol | Latest fundamental snapshot | PE | ROE | Dividend Yield |
|---|---|---:|---:|---:|---:|
| affected | AVGO | missing | NULL | NULL | NULL |
| affected | IBM | missing | NULL | NULL | NULL |
| affected | LLY | missing | NULL | NULL | NULL |
| affected | MA | missing | NULL | NULL | NULL |
| affected | MRK | missing | NULL | NULL | NULL |
| affected | ORCL | missing | NULL | NULL | NULL |
| affected | PG | missing | NULL | NULL | NULL |
| healthy | AAPL | 2026-06-04 | 37.2259 | 1.5191 | 0.003385 |
| healthy | AMZN | 2026-06-04 | 29.3960 | 0.1889 | 0.000000 |
| healthy | META | 2026-06-04 | 22.2645 | 0.2783 | 0.003386 |
| healthy | MSFT | 2026-06-04 | 25.1871 | 0.2965 | 0.008382 |
| healthy | NVDA | 2026-06-04 | 32.8743 | 0.7633 | 0.000185 |

Conclusion: values are not becoming zero in `fundamental_snapshots`; the rows are absent for affected symbols.

### Finding 3: Identical `47.25` scores are the scoring engine's missing-data path

Relevant code:

- `app/analytics/investor_scoring_engine.py:154` converts `None` fundamentals to `{}`.
- `app/analytics/investor_scoring_engine.py:39` `score_valuation()`: missing/invalid PE returns `45`.
- `app/analytics/investor_scoring_engine.py:55` `score_dividend()`: missing dividend yield returns `40`.
- `app/analytics/investor_scoring_engine.py:72` `score_financial_quality()`: starts at `50`; missing ROE/debt/FCF leave it at `50`.
- `app/analytics/investor_scoring_engine.py:112` `score_price_position()`: missing distance returns `50`.
- `app/analytics/investor_scoring_engine.py:129` `score_technical()`: missing technical confidence returns `50`.

Calculation:

```text
(45 * 0.25) + (40 * 0.15) + (50 * 0.30) + (50 * 0.15) + (50 * 0.15)
= 11.25 + 6.00 + 15.00 + 7.50 + 7.50
= 47.25
```

The recommendation threshold makes any score below `50` an `Avoid`.

Database investor score evidence for all affected symbols:

- `buy_score = 47.25`
- `recommendation = Avoid`
- `valuation_score = 45`
- `dividend_score = 40`
- `financial_quality_score = 50`
- `price_position_score = 50`
- `technical_score = 50`
- `raw_score.fundamentals_available = false`
- `raw_score.technical_available = false`

Conclusion: identical scores are confirmed default-path artifacts.

### Finding 4: Persistence preserves NULL and does not coalesce fundamentals to zero

Relevant code:

- `app/db/intelligence_persistence.py:148` `persist_fundamental_snapshot()`
- `app/db/intelligence_persistence.py:201` persists `fundamentals.get("pe_ratio")`
- `app/db/intelligence_persistence.py:203` persists `fundamentals.get("roe")`
- `app/db/intelligence_persistence.py:205` persists `fundamentals.get("dividend_yield")`
- `app/db/intelligence_persistence.py:214` `persist_investor_score()`
- `app/db/intelligence_persistence.py:268` persists `score.get("dividend_yield")`
- `app/db/intelligence_persistence.py:269` persists `score.get("pe_ratio")`

Schema inspection:

| Table | Column | Nullable | Default |
|---|---|---:|---|
| fundamental_snapshots | pe_ratio | YES | none |
| fundamental_snapshots | roe | YES | none |
| fundamental_snapshots | dividend_yield | YES | none |
| investor_scores | dividend_yield | YES | none |
| investor_scores | pe_ratio | YES | none |

Aggregate latest fundamental data:

| Total latest fundamental symbols | PE present | ROE present | Dividend present | PE zero | ROE zero | Dividend zero |
|---:|---:|---:|---:|---:|---:|---:|
| 23 | 18 | 18 | 18 | 0 | 0 | 3 |

Conclusion: no database default or persistence path converts missing PE/ROE/dividend values to zero.

### Finding 5: JSON export preserves NULL as null

Relevant code:

- `app/renderers/web_export.py:25` `_json_number()` returns `None` when input is `None`.
- `app/renderers/web_export.py:127` `_format_investor_row()`
- `app/renderers/web_export.py:138` exports `dividend_yield`
- `app/renderers/web_export.py:139` exports `pe_ratio`
- `app/renderers/web_export.py:140` exports `roe`
- `app/renderers/web_export.py:197` writes `web/data/investor-rankings.json`

Current `web/data/investor-rankings.json` evidence for AVGO:

```json
{
  "symbol": "AVGO",
  "buy_score": 47.25,
  "recommendation": "Avoid",
  "dividend_yield": null,
  "pe_ratio": null,
  "roe": null,
  "valuation_score": 45.0,
  "financial_quality_score": 50.0,
  "dividend_score": 40.0
}
```

Conclusion: export is not converting these fields to zero.

### Finding 6: Dashboard renders null as 0 / 0%

Relevant code:

- `web/index.html:716` `formatNumber(value)` calls `Number(value)`.
- `web/index.html:736` `formatPercent(value)` calls `Number(value)`.
- `web/index.html:880` renders dividend yield with `formatPercent(item.dividend_yield)`.
- `web/opportunity.html:334` `formatNumber(value)` calls `Number(value)`.
- `web/opportunity.html:343` `formatPercent(value)` calls `Number(value)`.
- `web/opportunity.html:440` renders PE Ratio.
- `web/opportunity.html:442` renders Dividend Yield.

JavaScript behavior:

```js
Number(null) === 0
```

Therefore JSON `null` displays as:

- PE Ratio: `0`
- ROE: `0%`
- Dividend Yield: `0%`

Conclusion: UI is masking backend nulls as real zeros.

## Where Values Become Zero

PE Ratio:

- FMP for affected symbols: no valid JSON due HTTP 402.
- Collector: returns `ERROR`, no PE value.
- Main pipeline: drops affected fundamental payload.
- Database: no fundamental row; investor score `pe_ratio` is `NULL`.
- JSON export: `pe_ratio` is `null`.
- Dashboard: `Number(null)` displays `0`.

ROE:

- Collector calculates ROE from income/balance via `_calculate_roe()` only after successful FMP responses.
- Affected symbols fail before parsing income/balance data.
- Database/export: `NULL`/`null`.
- Dashboard: `Number(null)` displays `0` / `0%`.

Dividend Yield:

- FMP ratios endpoint is inaccessible for affected symbols under current subscription behavior.
- Collector never maps `dividendYieldTTM`.
- Database/export: `NULL`/`null`.
- Dashboard: `Number(null)` displays `0%`.

Occurrences reviewed:

- `value or 0`: present in unrelated summary/ticker/report fallbacks, not the affected fundamental path.
- `float(value or 0)`: not found in affected fundamental/scoring/export path.
- `dict.get("field", 0)`: not found for PE/ROE/dividend in affected path.
- `COALESCE(..., 0)`: found in `app/db/migrate_investor_scores_phase2.sql` for legacy `buy_score`, not PE/ROE/dividend.
- `Number(value)`: found in dashboard formatters and is the source of displayed zeros for `null`.

## Data Quality Assessment

Current investor universe classification from latest database rows:

| Symbol | Data Completeness % | Missing Fields | Current Recommendation | Status |
|---|---:|---|---|---|
| AAPL | 100.00 |  | Watch | COMPLETE |
| AMD | 100.00 |  | Avoid | COMPLETE |
| AMZN | 100.00 |  | Buy | COMPLETE |
| AVGO | 0.00 | PE Ratio, ROE, Dividend Yield, Income Statement, Balance Sheet, Cash Flow | Avoid | MISSING |
| BAC | 100.00 |  | Buy | COMPLETE |
| CSCO | 100.00 |  | Watch | COMPLETE |
| CVX | 100.00 |  | Buy | COMPLETE |
| GOOGL | 100.00 |  | Buy | COMPLETE |
| IBM | 0.00 | PE Ratio, ROE, Dividend Yield, Income Statement, Balance Sheet, Cash Flow | Avoid | MISSING |
| JNJ | 100.00 |  | Buy | COMPLETE |
| JPM | 100.00 |  | Buy | COMPLETE |
| KO | 100.00 |  | Strong Buy | COMPLETE |
| LLY | 0.00 | PE Ratio, ROE, Dividend Yield, Income Statement, Balance Sheet, Cash Flow | Avoid | MISSING |
| MA | 0.00 | PE Ratio, ROE, Dividend Yield, Income Statement, Balance Sheet, Cash Flow | Avoid | MISSING |
| META | 100.00 |  | Buy | COMPLETE |
| MRK | 0.00 | PE Ratio, ROE, Dividend Yield, Income Statement, Balance Sheet, Cash Flow | Avoid | MISSING |
| MSFT | 100.00 |  | Buy | COMPLETE |
| NVDA | 100.00 |  | Buy | COMPLETE |
| ORCL | 0.00 | PE Ratio, ROE, Dividend Yield, Income Statement, Balance Sheet, Cash Flow | Avoid | MISSING |
| PEP | 100.00 |  | Buy | COMPLETE |
| PG | 0.00 | PE Ratio, ROE, Dividend Yield, Income Statement, Balance Sheet, Cash Flow | Avoid | MISSING |
| TSLA | 100.00 |  | Watch | COMPLETE |
| UNH | 100.00 |  | Buy | COMPLETE |
| V | 100.00 |  | Buy | COMPLETE |
| XOM | 100.00 |  | Buy | COMPLETE |

Note: current `web/data/data-health.json` reports `fundamentals_available = 18/25`, `complete_symbols = 14/25`, and flags all affected symbols as `PARTIAL` because investor scores exist even though fundamentals do not.

## Database Verification Queries

Current fundamentals:

```sql
SELECT
    symbol,
    pe_ratio,
    roe,
    dividend_yield
FROM fundamental_snapshots
ORDER BY snapshot_date DESC;
```

Current investor scores:

```sql
SELECT
    symbol,
    pe_ratio,
    roe,
    dividend_yield,
    buy_score,
    recommendation
FROM investor_scores
ORDER BY score_date DESC;
```

Affected-vs-healthy latest fundamentals:

```sql
WITH targets(symbol, group_name) AS (
    VALUES
        ('AAPL','healthy'), ('MSFT','healthy'), ('META','healthy'),
        ('NVDA','healthy'), ('AMZN','healthy'),
        ('AVGO','affected'), ('ORCL','affected'), ('IBM','affected'),
        ('MA','affected'), ('LLY','affected'), ('MRK','affected'), ('PG','affected')
)
SELECT
    t.group_name,
    t.symbol,
    f.snapshot_date,
    f.pe_ratio,
    f.roe,
    f.dividend_yield,
    f.debt_to_equity,
    f.free_cash_flow
FROM targets t
LEFT JOIN LATERAL (
    SELECT snapshot_date, pe_ratio, roe, dividend_yield, debt_to_equity, free_cash_flow
    FROM fundamental_snapshots
    WHERE symbol = t.symbol
    ORDER BY snapshot_date DESC
    LIMIT 1
) f ON TRUE
ORDER BY t.group_name, t.symbol;
```

Affected-vs-healthy latest investor scores:

```sql
WITH targets(symbol, group_name) AS (
    VALUES
        ('AAPL','healthy'), ('MSFT','healthy'), ('META','healthy'),
        ('NVDA','healthy'), ('AMZN','healthy'),
        ('AVGO','affected'), ('ORCL','affected'), ('IBM','affected'),
        ('MA','affected'), ('LLY','affected'), ('MRK','affected'), ('PG','affected')
)
SELECT
    t.group_name,
    t.symbol,
    s.score_date,
    s.pe_ratio,
    fs.roe,
    s.dividend_yield,
    s.buy_score,
    s.recommendation,
    s.valuation_score,
    s.dividend_score,
    s.financial_quality_score,
    s.price_position_score,
    s.technical_score,
    s.raw_score
FROM targets t
LEFT JOIN LATERAL (
    SELECT *
    FROM investor_scores
    WHERE symbol = t.symbol
    ORDER BY score_date DESC
    LIMIT 1
) s ON TRUE
LEFT JOIN LATERAL (
    SELECT roe
    FROM fundamental_snapshots
    WHERE symbol = t.symbol
    ORDER BY snapshot_date DESC
    LIMIT 1
) fs ON TRUE
ORDER BY t.group_name, t.symbol;
```

## Root Cause Analysis

| Candidate | Finding | Confidence |
|---|---|---|
| A) FMP data missing/inaccessible | True for affected symbols under current plan/API behavior; live endpoints return HTTP 402 / premium response. | HIGH |
| B) Collector mapping bug | Not primary. Mapping works for healthy symbols and tests cover FMP field names. Collector returns ERROR before mapping affected symbols. | HIGH |
| C) Database persistence bug | Not primary. Persistence preserves nullable values and no affected fundamental rows exist to persist. | HIGH |
| D) Scoring engine default-value bug | True contributor. Missing fundamentals are scored using deterministic defaults, producing identical `47.25 Avoid`. | HIGH |
| E) JSON export bug | Not primary. Export preserves nulls. | HIGH |
| F) Dashboard rendering bug | True contributor for visible `0`/`0%`; `Number(null)` masks null as zero. | HIGH |
| G) Combination | Yes: FMP access failure + scoring defaults + UI null formatting. | HIGH |

## Risk Assessment

Business impact:

- High. Investor Edition can issue `Avoid` recommendations for high-quality, dividend-paying companies solely because fundamentals were inaccessible.

Data integrity impact:

- Medium. Persisted data is not corrupted with fake zeros, but `investor_scores` persists recommendations based on missing inputs without enough gating.

User-facing impact:

- High. The dashboard displays missing metrics as `0`/`0%`, implying factual values rather than unavailable data.

Operational impact:

- Medium. Current data-health output warns about coverage, but scoring/export still allow incomplete symbols to appear as ranked opportunities.

## Recommended Fixes

Quick fix:

- Update dashboard formatters to treat `null`, `undefined`, and empty strings as unavailable before calling `Number(value)`.
- Display `N/A` or `--` for missing PE/ROE/dividend instead of `0`.
- Add a visible data completeness flag for ranked rows where `missing_data` is non-empty.

Proper fix:

- In the scoring engine, gate recommendations when required fundamentals are missing. Options:
  - return `Insufficient Data` instead of `Avoid`;
  - exclude missing-fundamental symbols from ranked opportunities;
  - persist a score row but mark `recommendation = "Insufficient Data"` and avoid normal buy-score ranking.
- Keep `raw_score.fundamentals_available` and add explicit missing-field metadata to `investor_scores.raw_score`.
- Update data-health classification so missing fundamentals are not hidden by the presence of an investor score.

Long-term improvement:

- Add collector-level diagnostics for HTTP 402/rate-limit/provider errors, including per-symbol status counts in `data-health.json`.
- Add fallback fundamentals provider or FMP endpoint fallback if current FMP plan cannot cover the full investor universe.
- Monitor required-field coverage before scoring and fail/warn the run when coverage drops below a threshold.
- Add regression tests for null rendering, missing-fundamental scoring, and FMP non-JSON/402 responses.
