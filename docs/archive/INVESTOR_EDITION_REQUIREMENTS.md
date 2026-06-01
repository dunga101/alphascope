# AlphaScope Investor Edition Requirements

## Objective

Transform AlphaScope from an intelligence platform into an investor decision-support platform.

## Must Have

### Fundamental Persistence

Persist collected fundamentals into:

fundamental_snapshots

Required fields:

- symbol
- snapshot_date
- pe_ratio
- roe
- debt_to_equity
- dividend_yield
- revenue_growth
- free_cash_flow

---

### Investor Scoring Engine

Create:

investor_scoring_engine.py

Generate:

1. Valuation Score
2. Dividend Score
3. Financial Quality Score
4. Price Position Score
5. Technical Score

Produce:

BUY_SCORE (0-100)

---

### Ranking

Rank all tracked symbols.

Highest BUY_SCORE first.

---

### Dashboard

Display:

- Symbol
- Company
- BUY_SCORE
- Recommendation
- Dividend Yield
- P/E
- Distance From 52 Week Low
- RSI
- Sector

---

### Recommendation Logic

BUY_SCORE >= 80

Strong Buy

BUY_SCORE >= 65

Buy

BUY_SCORE >= 50

Watch

Otherwise

Avoid

---

### Investor Focus

Primary investor profile:

Long-term investor seeking:

- quality companies
- dividend opportunities
- stocks trading below historical highs
- reasonable valuation

No automated trading.
No brokerage integration.
Research only.
