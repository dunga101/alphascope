# AlphaScope 📈🧠

### AI-Powered Investor Intelligence Platform

AlphaScope is a Python-based investment intelligence platform that combines market data, company fundamentals, technical analysis, AI reasoning, and historical persistence to identify and rank potential investment opportunities.

The platform transforms raw market information into structured investor-focused intelligence through a transparent scoring and recommendation engine.

AlphaScope is not a trading bot.

It is a decision-support platform designed to help investors identify quality opportunities using a disciplined, data-driven approach.

---

# Key Features

## Investor Scoring Engine

AlphaScope evaluates each company using multiple scoring dimensions:

* Valuation Score
* Financial Quality Score
* Dividend Score
* Technical Score
* Price Position Score

Scores are combined into a composite:

**BUY_SCORE (0-100)**

which drives investment recommendations.

---

## Investment Rankings

The platform ranks opportunities across a watchlist and generates:

* Strong Buy
* Buy
* Hold
* Watch
* Avoid

recommendations based on objective criteria.

---

## Technical Analysis

Per-symbol analysis includes:

* RSI
* SMA20
* SMA50
* SMA200
* ATR
* Volatility
* Relative Strength
* Distance From 52-Week Low
* Drawdown From 52-Week High

---

## Fundamental Analysis

AlphaScope collects and stores:

* P/E Ratio
* Revenue
* Net Income
* Free Cash Flow
* Return on Equity (ROE)
* Debt-to-Equity
* Dividend Yield

using Financial Modeling Prep (FMP).

---

## AI-Assisted Market Intelligence

Google Gemini provides:

* Executive summaries
* Market interpretation
* Risk analysis
* Opportunity commentary
* Investment narratives

AI is applied after deterministic analysis to ensure consistency and explainability.

---

## Historical Intelligence Database

All intelligence is stored in PostgreSQL.

Current persistence includes:

### intelligence_reports

Daily market intelligence.

### event_snapshots

Market events and catalysts.

### technical_snapshots

Per-symbol technical analysis history.

### fundamental_snapshots

Historical company fundamentals.

### investor_scores

Historical investment rankings and Buy Scores.

---

# Current Architecture

```text
Market Data Sources
        │
        ▼
Collection Layer
        │
        ▼
Technical Analysis
        │
        ▼
Fundamental Analysis
        │
        ▼
Investor Scoring Engine
        │
        ▼
Ranking Engine
        │
        ▼
Gemini Intelligence Layer
        │
        ▼
PostgreSQL Persistence
        │
        ▼
Dashboard & Reports
        │
        ▼
Telegram Delivery
```

---

# Technology Stack

## Languages

* Python

## Data Sources

* Yahoo Finance
* Financial Modeling Prep (FMP)
* Finnhub
* RSS Financial Feeds

## AI

* Google Gemini

## Database

* PostgreSQL

## Delivery

* Telegram Bot API

## Infrastructure

* Ubuntu Server
* VS Code Remote SSH
* GitHub
* Python Virtual Environments

---

# Project Structure

```text
alphascope/
│
├── app/
│   ├── ai/
│   ├── analytics/
│   ├── collectors/
│   ├── config/
│   ├── db/
│   ├── processors/
│   ├── renderers/
│   └── main.py
│
├── reports/
├── web/
├── requirements.txt
└── README.md
```

---

# Current Development Status

## Completed

✅ Market Intelligence Engine

✅ Technical Analysis Engine

✅ Fundamental Data Collection

✅ Historical PostgreSQL Persistence

✅ AI Intelligence Layer

✅ Investor Scoring Engine

✅ Investment Ranking Engine

✅ Historical Investor Score Tracking

---

## In Progress

🔄 Investor Dashboard

Active Sprint 1 requirements and implementation scope:

* [Investor Dashboard V2](docs/INVESTOR_DASHBOARD_V2.md)

Historical planning and superseded requirements:

* [Documentation Archive](docs/archive/)

Planned dashboard features:

* Ranked Opportunities
* Buy Scores
* Recommendation Transparency
* Historical Score Trends
* Technical/Fundamental Breakdown
* Investor-Friendly Interface

---

# Future Roadmap

## Phase 1 (Current)

Investor Dashboard

## Phase 2

Opportunity Alerts

## Phase 3

Confidence Calibration Engine

## Phase 4

Prediction Accuracy Tracking

## Phase 5

Family Investment Portal

## Phase 6

Portfolio Analytics

---

# Setup

## Clone Repository

```bash
git clone https://github.com/dunga101/alphascope.git
cd alphascope
```

## Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Configure Environment Variables

Create:

```env
.env
```

Example:

```env
GEMINI_API_KEY=
FMP_API_KEY=
FINNHUB_API_KEY=

DB_HOST=
DB_NAME=alphascope
DB_USER=
DB_PASSWORD=
DB_PORT=5432

TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

---

# Run AlphaScope

```bash
python -m app.main
```

---

# Disclaimer

AlphaScope is an educational and engineering project.

It does not provide financial or investment advice.

Users remain solely responsible for all investment decisions.

---

# Author

### Dulanga Mudalige

Mechanical Engineer | Infrastructure Engineer | Cloud | Security | Automation

GitHub:
https://github.com/dunga101

LinkedIn:
https://www.linkedin.com/in/dulanga-mudalige
