# AlphaScope Missing Fundamentals Fix Plan

Generated: 2026-06-04

## Objective

Prevent missing fundamentals from producing misleading `Avoid` recommendations and prevent dashboard `null` values from rendering as `0` / `0%`.

No fixes have been implemented in this investigation.

## Files To Modify

1. `web/index.html`
2. `web/opportunity.html`
3. `app/analytics/investor_scoring_engine.py`
4. `app/analytics/test_investor_scoring_engine.py`
5. `app/renderers/test_web_export.py` or new frontend-focused formatter tests if a JS test harness is added
6. Optional: `app/renderers/web_export.py`
7. Optional: `app/collectors/fmp_fundamentals.py`

## Expected Code Changes

### Dashboard Null Formatting

Functions:

- `web/index.html`: `formatNumber()`, `formatCurrency()`, `formatPercent()`
- `web/opportunity.html`: `formatNumber()`, `formatCurrency()`, `formatPercent()`, `formatPercentPoints()`

Change:

- Add an explicit unavailable check before `Number(value)`.
- Treat `null`, `undefined`, and `''` as `--`.
- Continue displaying real numeric `0` as `0` / `0%`.

Expected behavior:

| Input | Current display | New display |
|---|---|---|
| `null` | `0` / `0%` | `--` |
| `undefined` | `--` | `--` |
| `0` | `0` / `0%` | `0` / `0%` |

### Missing-Fundamental Scoring Gate

Functions:

- `app/analytics/investor_scoring_engine.py`: `score_investor_opportunity()`

Change:

- Detect required fundamental gaps before normal scoring.
- Required fields should include at least `pe_ratio`, `roe`, `debt_to_equity`, `dividend_yield`, and `free_cash_flow`.
- If required fundamentals are unavailable, set a non-investable recommendation such as `Insufficient Data` instead of `Avoid`.
- Preserve component score values only if needed for diagnostics, but avoid treating default score `47.25` as a real investment ranking.

Suggested output additions:

```python
"data_status": "INSUFFICIENT_FUNDAMENTALS",
"missing_fundamental_fields": [...],
```

### Export/Data Health Improvements

Functions:

- `app/renderers/web_export.py`: `_format_investor_row()`, `_build_data_health_row()`, `_health_status()`

Change:

- Include `data_status` and `missing_fundamental_fields` in `investor-rankings.json`.
- Classify symbols with investor scores but no fundamentals as `MISSING_FUNDAMENTALS` or equivalent, not broadly `PARTIAL`.

### Collector Diagnostics

Functions:

- `app/collectors/fmp_fundamentals.py`: `collect_fundamentals()`

Change:

- Preserve provider error type/status in the collector result, especially HTTP 402.
- Redact API keys from error strings before returning/logging.
- Optional: detect known premium/subscription response text and return structured reason:

```python
{
    "status": "ERROR",
    "symbol": symbol,
    "error_type": "FMP_PAYMENT_REQUIRED",
    "reason": "FMP endpoint unavailable under current subscription"
}
```

## Testing Plan

Unit tests:

- Add a scoring test for missing fundamentals:
  - input `fundamentals=None`
  - expected `raw_score.fundamentals_available == False`
  - expected recommendation `Insufficient Data` or chosen equivalent
  - expected no misleading normal `Avoid` classification
- Add a scoring test where real zero dividend yield remains valid for non-dividend stocks.
- Add collector test for HTTP 402:
  - mock `requests.get().raise_for_status()` raising 402
  - verify result is structured and redacts API key.
- Add export test that JSON keeps `null` and includes missing-data metadata.

Manual verification:

```sql
SELECT
    symbol,
    pe_ratio,
    roe,
    dividend_yield,
    buy_score,
    recommendation,
    raw_score
FROM investor_scores
WHERE symbol IN ('AVGO','ORCL','IBM','MA','LLY','MRK','PG')
ORDER BY score_date DESC, symbol;
```

Dashboard verification:

- Open `web/index.html`.
- Confirm affected symbols display `--` for PE/ROE/dividend where values are unavailable.
- Confirm `AMZN` or any true zero dividend value still displays `0%`.
- Confirm affected symbols are clearly marked as insufficient-data rows.

## Regression Risks

- Changing `Avoid` to `Insufficient Data` may require CSS/status handling wherever recommendation badges are displayed.
- Excluding insufficient-data symbols from ranking could change ranking counts and top-opportunity summaries.
- Treating `null` differently in JS must not hide true numeric zero values.
- Adding stricter scoring gates may affect historical comparisons in `investor_scores`.

## Rollback Plan

- Revert the dashboard formatter changes if display regressions occur.
- Revert scoring gate changes independently if recommendation status handling breaks downstream consumers.
- Keep any collector diagnostics additive so rollback does not require schema changes.

## Deployment Considerations

- No database schema change is required for the quick fix.
- If `data_status` is added only inside `raw_score` or JSON export, deployment remains backward compatible.
- Coordinate with FMP subscription/provider decision separately; code fixes can prevent misleading output but cannot restore unavailable FMP data.
