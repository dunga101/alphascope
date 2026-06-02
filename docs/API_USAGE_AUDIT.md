# AlphaScope API Usage Audit

Date: 2026-06-01

Scope: audit only. No application code, configuration, or symbol universe changes were made.

## Executive Summary

AlphaScope currently runs a serial, report-centric pipeline. With the current 7-symbol investor universe, recent logged full runs completed in about 29-34 seconds when FMP quote/profile/fundamental caches were warm.

The largest scale risk before expanding the investor universe is not Gemini call count. Gemini currently runs as two global calls per full run. The largest scale risks are:

- FMP request growth from quote, profile, and fundamentals calls.
- Yahoo Finance request growth if earnings and technical analysis are expanded across the full universe.
- Runtime growth from serial HTTP requests.
- Prompt/token growth if all per-symbol fundamentals are sent to Gemini.

Recommendation: Sprint 1 should not run full AI analysis on every symbol. Use a two-stage architecture:

1. Universe -> deterministic data collection and scoring.
2. Top candidates -> dashboard, Telegram, and any future Gemini narrative.

Recommended Sprint 1 rollout size: 25 symbols initially, then 50 after cache, quota, and runtime validation.

## Current External APIs And Data Sources

### Financial Modeling Prep (FMP)

Active in `python -m app.main full` through `collect_fmp_layer()`:

- `app/collectors/fmp_quotes.py`
  - Endpoint: `https://financialmodelingprep.com/stable/quote`
  - One request per `FMP_WATCHLIST` symbol.
  - Cache: `data/cache/fmp_{SYMBOL}.json`
  - TTL: `FMP_CACHE_MINUTES`, default 30 minutes.

- `app/collectors/fmp_profile.py`
  - Endpoint: `https://financialmodelingprep.com/stable/profile`
  - One request per `FMP_WATCHLIST` symbol.
  - Cache: `data/cache/fmp_profiles/{SYMBOL}.json`
  - TTL: `FMP_PROFILE_CACHE_HOURS`, default 168 hours.

- `app/collectors/fmp_fundamentals.py`
  - Endpoints per symbol:
    - `stable/income-statement`
    - `stable/balance-sheet-statement`
    - `stable/cash-flow-statement`
    - `stable/ratios-ttm`
  - Four requests per `FUNDAMENTAL_SYMBOLS` symbol.
  - Cache: `data/cache/fmp_fundamentals/{SYMBOL}.json`
  - TTL: `FMP_FUNDAMENTAL_CACHE_HOURS`, default 24 hours.
  - Cache is used only if required investor fields are present.

FMP modules present but not active in `app.main`:

- `app/collectors/fmp_news.py`
- `app/db/fmp_price_seed.py`
- `app/db/fmp_seed_loader.py`
- `app/db/fmp_reference_seed.py`

### Finnhub

Active in `python -m app.main full` through `collect_news_intelligence()`:

- `app/collectors/finnhub_news.py`
  - Endpoint: `https://finnhub.io/api/v1/news`
  - One global request per run.
  - Category: `general`
  - Limit applied locally to 30 articles.
  - Cache: none.

### Yahoo Finance / `yfinance`

Active in multiple places:

- `app/renderers/report.py`
  - `collect_advanced_breadth()`: 4 symbols.
  - `collect_macro_signals()`: 8 symbols.
  - technical report `WATCHLIST`: 10 symbols.

- `app/main.py`
  - `collect_macro_context(MACRO_SYMBOLS)`: 8 symbols.
  - `collect_sector_breadth(SECTOR_SYMBOLS)`: 10 symbols.
  - `collect_earnings_context(CORE_SYMBOLS)`: current 7 symbols.

- `app/processors/indicators.py`
  - One `Ticker.history(period="6mo")` call per technical-report watchlist symbol.

Cache: no project-level cache for yfinance calls in the active pipeline.

Important distinction:

- Investor ranking technical metrics from `app/analytics/technical_engine.py` are database-backed from `market_prices`; they do not call Yahoo Finance directly.
- The fixed technical report generation does call Yahoo Finance.

### Google Gemini

Active in `python -m app.main full`:

- `app/ai/news_analyzer.py`
  - Model: `gemini-2.5-flash`
  - One global event-intelligence call if news events exist.

- `app/ai/gemini_client.py`
  - Model: `gemini-2.5-flash-lite`
  - One global market-analysis call.

Cache: none.

Mode behavior:

- `full`: two Gemini calls when news events are available.
- `degraded`: FMP is disabled, but Gemini still runs.
- `offline`: Gemini is bypassed.

### RSS Feeds

Active in `python -m app.main full` through `collect_news_intelligence()`:

- `app/collectors/rss_news.py`
  - CNBC Markets
  - MarketWatch Top Stories
  - Reuters Business/Finance
  - Yahoo Finance RSS

Requests:

- Four global feed fetches per run.
- Local limit: 10 entries per feed.
- Artificial delay: `time.sleep(0.5)` per feed, so RSS collection adds at least about 2 seconds.
- Cache: none.

### Telegram

Not a market data source, but it is an external API used during `app.main`:

- `app/renderers/telegram.py`
  - One `sendMessage` POST per successful run.
  - Cache: none.

## Complete Execution Path: `python -m app.main full`

1. Parse mode.
2. Generate technical report:
   - Yahoo Finance advanced breadth: 4 history calls.
   - Yahoo Finance macro signals: 8 history calls.
   - Yahoo Finance technical watchlist: 10 history calls.
3. Collect macro context:
   - Yahoo Finance macro symbols: 8 history calls.
4. Collect sector breadth:
   - Yahoo Finance sector ETFs: 10 history calls.
5. Collect earnings context:
   - Yahoo Finance earnings dates for each `CORE_SYMBOLS` symbol.
6. Collect FMP layer:
   - FMP quotes for `FMP_WATCHLIST`.
   - FMP profiles for `FMP_WATCHLIST`.
   - FMP fundamentals for `FUNDAMENTAL_SYMBOLS`.
7. Collect event intelligence:
   - Finnhub general market news: 1 request.
   - RSS feeds: 4 requests.
   - Local news fusion.
8. Run Gemini event synthesis:
   - 1 Gemini call unless offline or no news events.
9. Run Gemini market analysis:
   - 1 Gemini call unless offline.
10. Persist market, technical, fundamental, investor score, intelligence, and event snapshots.
11. Build investor rankings:
   - Current implementation uses FMP data already collected.
   - Per-symbol technical indicators are read from PostgreSQL, not an external API.
12. Export static web JSON:
   - `latest-report.json`
   - `full-report.json`
   - `investor-rankings.json`
13. Send Telegram summary:
   - 1 Telegram API request.

## Current 7-Symbol Universe Usage Estimate

Current symbol config:

- `CORE_SYMBOLS`: 7 symbols.
- `FMP_WATCHLIST`: `SPY` plus 7 core symbols = 8 symbols.
- `FUNDAMENTAL_SYMBOLS`: 7 symbols.
- technical report `WATCHLIST`: fixed 10 symbols.

### Per Full Run, Cold FMP Cache

| Source | Calls |
|---|---:|
| FMP quotes | 8 |
| FMP profiles | 8 |
| FMP fundamentals | 28 |
| FMP total | 44 |
| Finnhub | 1 |
| RSS feeds | 4 |
| Yahoo Finance history/earnings request groups | about 47 |
| Gemini | 2 |
| Telegram | 1 |

Yahoo Finance request groups are estimated as:

- 4 advanced breadth
- 8 macro signals
- 10 technical report watchlist
- 8 macro context
- 10 sector breadth
- 7 earnings lookups

### Per Full Run, Warm FMP Cache

| Source | Calls |
|---|---:|
| FMP quotes | 0 if within 30-minute quote cache, otherwise 8 |
| FMP profiles | 0 if within 168-hour profile cache |
| FMP fundamentals | 0 if within 24-hour fundamentals cache and required fields exist |
| Finnhub | 1 |
| RSS feeds | 4 |
| Yahoo Finance history/earnings request groups | about 47 |
| Gemini | 2 |
| Telegram | 1 |

Recent automation logs on 2026-06-01 show full runs completing in:

- 29.06 seconds
- 34.16 seconds
- 32.22 seconds

Those runs show the FMP layer completing almost instantly, consistent with warm caches.

## Scaling Projections

The following projections assume the investor universe expands to `N` symbols and the architecture keeps the same shape:

- `FMP_WATCHLIST = SPY + N`
- `FUNDAMENTAL_SYMBOLS = N`
- earnings context scales with `N`
- technical report `WATCHLIST` remains fixed at 10 symbols
- Gemini remains two global calls

### Per-Run Call Formulas

| Source | Formula |
|---|---:|
| FMP quotes | `N + 1` |
| FMP profiles | `N + 1` |
| FMP fundamentals | `4N` |
| FMP total, cold cache | `6N + 2` |
| FMP total, warm same-run cache | `0` to `N + 1`, depending on quote TTL |
| Finnhub | `1` |
| RSS feeds | `4` |
| Yahoo Finance | `40 + N` |
| Gemini | `2` |
| Telegram | `1` |

### Estimated Calls By Universe Size

| Universe | FMP cold cache | FMP quote-only refresh | Yahoo Finance | Finnhub | RSS | Gemini |
|---:|---:|---:|---:|---:|---:|---:|
| 7 | 44 | 8 | 47 | 1 | 4 | 2 |
| 25 | 152 | 26 | 65 | 1 | 4 | 2 |
| 50 | 302 | 51 | 90 | 1 | 4 | 2 |
| 100 | 602 | 101 | 140 | 1 | 4 | 2 |

### Three Runs Per Day Estimate

Assuming three runs are spaced more than 30 minutes apart, profiles remain cached, and fundamentals refresh once per day:

| Universe | Approx FMP calls/day |
|---:|---:|
| 7 | 60 |
| 25 | 204 |
| 50 | 404 |
| 100 | 804 |

Formula: first run `6N + 2`, subsequent two runs quote-only `2(N + 1)`, total `8N + 4`.

If profile cache expires on a given day, add `N + 1` FMP calls.

## Runtime Impact

Observed current 7-symbol runtime with warm FMP cache: about 30-35 seconds.

Main runtime contributors today:

- Yahoo Finance earnings context: about 10 seconds for 7 symbols in recent logs.
- RSS collection: at least 2 seconds due to explicit sleeps.
- Gemini event synthesis: about 6-12 seconds in recent logs.
- Gemini market analysis: about 3-5 seconds in recent logs.
- FMP layer: near-zero when cached, potentially much higher when cold because calls are serial.

Estimated runtime by universe size:

| Universe | Warm-cache estimate | Cold-cache risk |
|---:|---:|---|
| 7 | 30-35 sec observed | 1-3 min depending on FMP latency |
| 25 | 1-2 min | 3-6 min |
| 50 | 2-4 min | 6-12 min |
| 100 | 4-8 min | 12-25+ min |

These are engineering estimates from code shape and observed logs, not live benchmark results. Actual runtime will depend heavily on FMP, Yahoo Finance, Gemini latency, retries, and API throttling.

## Bottlenecks And Scalability Limits

### API Quotas

FMP is the primary quota bottleneck.

- Fundamentals cost four FMP calls per symbol on a cold or expired cache.
- Quotes cost one FMP call per symbol every quote cache window.
- A 50-symbol universe can require about 302 FMP calls on a cold run and about 404 FMP calls across three daily runs.

Finnhub is low pressure in the current architecture.

- One global news request per run.
- Does not scale with universe size.

Yahoo Finance is a reliability and throttling bottleneck.

- The active pipeline has no project-level yfinance cache.
- Calls are serial and may be throttled or return empty data.
- If technical report generation is later expanded to all investor symbols, Yahoo Finance growth becomes much steeper.

### Runtime Growth

Runtime grows mostly from serial per-symbol work:

- FMP quote/profile/fundamental calls.
- Yahoo earnings calls.
- Any future per-symbol yfinance technical calls.

Current implementation is not optimized for large universes because it does not batch, parallelize, or rate-limit external calls centrally.

### Gemini Cost Growth

Gemini call count is currently constant at two calls per full run.

However, Gemini token cost can still grow if the prompt includes all per-symbol quote, profile, fundamentals, and technical report text. Expanding from 7 to 50 or 100 names can materially increase prompt size even without increasing call count.

Gemini should receive summarized top candidates and market context, not a full raw universe dump.

### Database Growth

Expected daily row growth for investor-related persistence:

- `fundamental_snapshots`: about `N` rows per day.
- `investor_scores`: about `N` rows per day.
- `technical_snapshots`: currently fixed around 10 rows per day unless technical report watchlist expands.
- `market_prices`: not populated by `app.main`; seed/reference scripts are separate.

Approximate annual investor rows:

| Universe | fundamental rows/year | investor score rows/year | combined/year |
|---:|---:|---:|---:|
| 25 | 9,125 | 9,125 | 18,250 |
| 50 | 18,250 | 18,250 | 36,500 |
| 100 | 36,500 | 36,500 | 73,000 |

This is manageable for PostgreSQL, but indexes, retention, and query patterns should be reviewed before historical charts are expanded.

### Web Export Size

`investor-rankings.json` scales roughly linearly with universe size.

Expected size risk is low for 25-100 symbols if each row remains compact. The larger risk is adding verbose per-symbol explanations, raw payloads, or historical time series into the same file.

Recommendation:

- Keep ranking JSON compact.
- Put verbose detail or history in separate files only if needed.
- Do not embed full raw FMP/Gemini payloads in the homepage JSON.

## Full Analysis Versus Two-Stage Ranking

The current architecture should not use full analysis on every symbol as the universe grows.

Recommended architecture:

1. Collect core deterministic data for the full universe.
2. Persist fundamentals and scores for all eligible symbols.
3. Rank all symbols using deterministic scoring.
4. Select top candidates for:
   - dashboard highlights
   - Telegram summary
   - any future Gemini narrative
5. Keep the Analyst Dashboard focused on market context plus top opportunities, not raw analysis for every symbol.

Why:

- FMP and Yahoo usage grow per symbol.
- Gemini prompt size grows with raw universe text.
- Users need ranked decisions, not 100 equally detailed narratives.
- Two-stage ranking preserves explainability and keeps AI spend bounded.

## Recommendations

### Safe Universe Size Today

Safe today: 25 symbols.

Reasoning:

- About 152 FMP calls on a cold run.
- About 204 FMP calls/day for three runs if fundamentals refresh once daily.
- Yahoo Finance request groups rise to about 65 per run.
- Runtime likely remains acceptable with current serial architecture.

### Safe Universe Size With Current Free-Tier Limits

Likely safe upper bound: 25 symbols unless the exact FMP and Gemini free-tier quotas are verified.

Conditional upper bound: 50 symbols if:

- FMP daily quota comfortably supports about 400+ calls/day.
- FMP cache hit rates are monitored.
- Failed symbols do not block the run.
- Runtime target allows several minutes per run.
- Gemini prompts are kept summarized.

100 symbols is not recommended on the current serial architecture.

### Recommended Sprint 1 Rollout Size

Recommended Sprint 1 rollout:

1. Start with 25 investor symbols.
2. Run at normal automation cadence for several cycles.
3. Review:
   - FMP cache hit/miss counts.
   - total run duration.
   - failed symbols.
   - generated JSON size.
   - Telegram usefulness.
4. Expand to 50 only after runtime and quota behavior are confirmed.

Avoid expanding directly to 100 symbols until the pipeline has:

- batching or concurrency with rate limits,
- stronger retry/backoff behavior,
- explicit API usage logging,
- cache metrics,
- and a two-stage Gemini prompt strategy.

## Immediate Non-Code Operational Guidance

- Before expanding symbols, confirm actual FMP plan limits for daily calls and rate limits.
- Treat current observed runtime as warm-cache runtime, not cold-start runtime.
- Monitor `fmp_quotes` cache stats already returned by the quote collector.
- Add future audit logging for profile and fundamentals cache hit/miss counts before scaling beyond 25-50 symbols.
- Keep Gemini analysis global and top-candidate oriented.
