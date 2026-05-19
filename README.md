# AlphaScope 📈🧠

**AI-assisted modular market intelligence platform for structured market analysis, catalyst awareness, and decision-support intelligence.**

AlphaScope transforms fragmented market data into disciplined, institutional-style intelligence by combining structured financial data, macro regime analysis, technical screening, event awareness, and AI-powered synthesis.

It is designed as an engineering-driven intelligence platform—not a hype-driven trading bot.

---

# Philosophy

Modern markets produce overwhelming amounts of data:

- price action
- macroeconomic signals
- earnings catalysts
- sector rotation
- news flow
- analyst sentiment
- volatility signals

Raw information is abundant.

Actionable intelligence is scarce.

AlphaScope exists to bridge that gap.

Its purpose is to ingest noisy market data, filter signal from distraction, and produce structured daily intelligence that supports rational decision-making.

---

# Current Capabilities

## Market Regime Intelligence

AlphaScope evaluates overall market conditions using macro market proxies:

- S&P 500 (`^GSPC`)
- Nasdaq 100 (`^NDX`)
- Dow Jones (`^DJI`)
- Russell 2000 (`^RUT`)
- VIX (`^VIX`)
- US 10Y Treasury Yield (`^TNX`)
- Gold
- Oil
- Bitcoin (market sentiment proxy)

It classifies market conditions into regimes such as:

- Risk-On
- Neutral
- Risk-Off
- Strong Risk-Off

with confidence scoring and tactical bias interpretation.

---

## Technical Screening Engine

Watchlist securities are analyzed using technical indicators:

- RSI
- moving averages
- momentum scoring
- volume confirmation
- signal classification

Current watchlist examples:

- SPY
- QQQ
- NVDA
- MSFT
- AMD
- TSLA
- GOOGL
- META
- SHOP
- AMZN

AlphaScope identifies:

- strong candidates
- overheated names
- weak names
- neutral setups

---

## Sector Rotation Intelligence

Sector ETF monitoring detects leadership changes across:

- XLK
- XLF
- XLI
- XLY
- XLU
- XLRE
- XLC
- XLV
- XLP
- XLE

Used for identifying:

- sector leadership
- defensive rotation
- cyclical weakness
- broad market participation

---

## Structured Financial Intelligence (FMP)

Integrated Financial Modeling Prep (FMP) data sources provide:

- live quote intelligence
- company profile data
- structured fundamentals
- valuation context
- company metadata

This layer supports higher-quality contextual interpretation beyond pure technical analysis.

---

## News Intelligence Pipeline

AlphaScope now includes a structured catalyst awareness engine.

### Finnhub Integration

Ticker-specific financial news ingestion:

- earnings catalysts
- analyst commentary
- event-driven headlines
- major corporate developments

---

### Signal Filtering

Raw news feeds are aggressively filtered.

Implemented controls include:

- ticker relevance validation
- alias matching
- junk suppression
- clickbait rejection
- crypto noise suppression
- low-signal opinion filtering
- catalyst prioritization

Goal:

AI receives meaningful signal—not random finance content.

---

## AI Intelligence Layer

Google Gemini is used as AlphaScope's reasoning engine.

Responsibilities:

- interpreting structured signals
- synthesizing macro + technical context
- identifying tactical risks
- generating executive summaries
- producing institutional-style commentary

AlphaScope is explicitly designed as:

**decision-support intelligence**

NOT:

- automated trade execution
- high-frequency trading
- meme-stock speculation
- retail hype commentary

---

## Automated Delivery

Current:

✅ Telegram delivery

Planned:

- HTML email reports
- scheduled distribution
- watchlist-specific delivery
- dashboard interface

---

# Architecture

```text
AlphaScope
│
├── app/
│   │
│   ├── ai/
│   │   └── gemini_client.py
│   │
│   ├── collectors/
│   │   ├── advanced_breadth.py
│   │   ├── earnings.py
│   │   ├── macro.py
│   │   ├── fmp_quotes.py
│   │   ├── fmp_profile.py
│   │   ├── fmp_fundamentals.py
│   │   ├── fmp_news.py
│   │   └── finnhub_news.py
│   │
│   ├── config/
│   │   └── ticker_aliases.py
│   │
│   ├── processors/
│   │   ├── indicators.py
│   │   ├── regime.py
│   │   ├── screener.py
│   │   └── news_filter.py
│   │
│   ├── renderers/
│   │   ├── report.py
│   │   └── telegram.py
│   │
│   └── main.py
│
├── data/
├── reports/
├── .env
├── requirements.txt
└── README.md
```

---

# Example Intelligence Workflow

```text
Market data collection
        ↓
Macro regime scoring
        ↓
Technical screening
        ↓
Financial context enrichment
        ↓
News catalyst ingestion
        ↓
Signal filtering / relevance validation
        ↓
AI reasoning & synthesis
        ↓
Markdown report generation
        ↓
Telegram delivery
```

---

# Technology Stack

## Language

- Python 3.x

---

## Market Data

- yfinance
- Financial Modeling Prep (FMP)
- Finnhub

---

## AI

- Google Gemini API

---

## Messaging

- Telegram Bot API

---

## Core Libraries

- requests
- pandas
- python-dotenv
- finnhub-python

---

## Infrastructure

Deployed and developed on:

- Ubuntu Server
- Python virtual environments
- GitHub
- homelab infrastructure

---

# Setup

## Clone repository

```bash
git clone https://github.com/dunga101/alphascope.git
cd alphascope
```

---

## Create environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## Install dependencies

```bash
pip install -r requirements.txt
```

---

## Configure environment

Create:

```bash
.env
```

Example:

```env
GEMINI_API_KEY=your_key
FMP_API_KEY=your_key
FINNHUB_API_KEY=your_key
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

# Running AlphaScope

Generate intelligence report:

```bash
python -m app.renderers.report
```

Run full pipeline:

```bash
python -m app.main
```

---

# Roadmap

## Phase 4 (In Progress)

### News Intelligence Expansion

Planned:

- RSS redundancy layer
- Reuters feed integration
- Yahoo Finance feed integration
- MarketWatch integration
- multi-source news fusion

---

## Phase 5

### Macro Intelligence Expansion

Planned integration:

- FRED economic data

Examples:

- CPI
- Core CPI
- unemployment
- Fed funds rate
- GDP
- yield curve
- consumer sentiment
- jobless claims

---

## Phase 6

### Corporate Event Intelligence

Planned:

SEC EDGAR integration

Examples:

- 8-K filings
- executive departures
- share issuance
- litigation
- acquisitions
- insider disclosures

---

## Phase 7

### Market Sentiment Intelligence

Potential integrations:

- CBOE volatility data
- options sentiment
- put/call ratios
- volatility term structure

---

## Phase 8

### Historical Intelligence Platform

Planned:

database-backed historical market intelligence

Potential capabilities:

- signal calibration
- regime comparison
- historical analytics
- performance validation
- eventual ML experimentation

---

# Design Principles

AlphaScope follows several design rules:

- modular architecture
- API cost discipline
- cache-aware engineering
- signal-over-noise filtering
- deterministic preprocessing before AI reasoning
- decision-support over speculation
- infrastructure-first engineering mindset

---

# Disclaimer

AlphaScope is an educational / engineering intelligence project.

It does **not** provide financial advice.

Users remain responsible for their own investment decisions.

---

# Author

**Dulanga Mudalige**

Infrastructure | Cloud | Security | Automation | Systems Engineering

GitHub:

https://github.com/dunga101