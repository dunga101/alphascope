# AlphaScope 📈🧠

**AI-assisted financial market intelligence platform engineered for structured analysis, catalyst awareness, and disciplined decision-support.**

AlphaScope is a modular Python-based market intelligence system that transforms fragmented financial data into structured, interpretable intelligence.

It combines deterministic market data processing, structured financial enrichment, event-aware news intelligence, confidence governance, and AI synthesis to produce institutional-style daily market intelligence reports.

This is an engineering portfolio project focused on systems design, modular architecture, API integration, data processing, and intelligent automation.

**AlphaScope is not a trading bot.**
It is an intelligence platform.

---

# Why AlphaScope Exists

Modern financial markets generate overwhelming volumes of data:

- macroeconomic signals
- price action
- volatility shifts
- earnings events
- analyst revisions
- news catalysts
- sector rotation
- sentiment proxies

Raw information is abundant.

Actionable intelligence is scarce.

AlphaScope exists to bridge that gap through disciplined engineering.

Its purpose is to collect, normalize, filter, enrich, and synthesize noisy market inputs into rational daily intelligence.

---

# Core Capabilities

## Market Regime Intelligence

AlphaScope evaluates broad market conditions using macro proxies including:

- S&P 500 (`^GSPC`)
- Nasdaq 100 (`^NDX`)
- Dow Jones (`^DJI`)
- Russell 2000 (`^RUT`)
- VIX (`^VIX`)
- US 10Y Treasury Yield (`^TNX`)
- Gold
- Oil
- Bitcoin

This enables regime classification such as:

- Risk-On
- Neutral
- Risk-Off
- Strong Risk-Off

Outputs include:

- market regime classification
- confidence scoring
- tactical bias interpretation
- macro context awareness

---

## Technical Screening Engine

Watchlist securities are analyzed using technical indicators such as:

- RSI
- moving averages
- momentum classification
- volume confirmation
- signal scoring

Example watchlist:

- SPY
- QQQ
- NVDA
- MSFT
- AMD
- TSLA
- GOOGL
- META
- AMZN
- SHOP

AlphaScope identifies:

- strong setups
- overheated conditions
- weak technical structures
- neutral opportunities

---

## Sector Rotation Intelligence

ETF breadth monitoring tracks sector leadership:

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

Used for:

- leadership detection
- defensive rotation awareness
- cyclical weakness identification
- participation analysis

---

## Structured Financial Intelligence

AlphaScope integrates Financial Modeling Prep (FMP) data sources for:

- live quotes
- company profiles
- structured fundamentals
- valuation context
- company metadata
- financial statement intelligence

This improves contextual quality beyond pure technical analysis.

---

## Event Intelligence Pipeline

AlphaScope includes structured event-aware intelligence.

Data sources include:

- Finnhub financial news
- curated RSS financial feeds
- structured catalyst filtering

Capabilities:

- earnings event awareness
- analyst commentary ingestion
- headline relevance scoring
- ticker alias matching
- junk suppression
- crypto noise filtering
- clickbait rejection

Goal:

AI receives curated signal, not random internet noise.

---

## Confidence Governance Engine

AlphaScope uses a layered confidence framework that separates:

- market regime confidence
- event-driven confidence
- weighted confidence fusion

This avoids simplistic "AI says buy" logic and enforces deterministic signal governance before AI interpretation.

---

## AI Intelligence Layer

Google Gemini is used strictly as a reasoning layer.

Responsibilities:

- macro interpretation
- signal synthesis
- executive commentary generation
- risk identification
- contextual summarization
- decision-support narrative generation

AI operates *after deterministic preprocessing*.

This architecture intentionally prevents raw, noisy AI prompting.

---

## Automated Delivery

Current delivery:

✅ Telegram intelligence delivery

Planned delivery:

- HTML email reports
- scheduled daily distribution
- dashboard UI
- watchlist personalization

---

# Engineering Highlights

AlphaScope demonstrates:

- modular Python architecture
- API integration engineering
- caching strategies
- retry logic
- signal preprocessing
- structured data normalization
- AI integration
- environment-based secret management
- automation workflows
- quota-aware API consumption design
- report generation pipelines

---

# Architecture

```text
AlphaScope
│
├── app/
│   ├── ai/
│   │   ├── gemini_client.py
│   │   └── news_analyzer.py
│   │
│   ├── collectors/
│   │   ├── advanced_breadth.py
│   │   ├── analyst.py
│   │   ├── breadth.py
│   │   ├── earnings.py
│   │   ├── finnhub_news.py
│   │   ├── fmp_fundamentals.py
│   │   ├── fmp_news.py
│   │   ├── fmp_profile.py
│   │   ├── fmp_quotes.py
│   │   ├── insider.py
│   │   ├── macro.py
│   │   ├── macro_signals.py
│   │   ├── news_intelligence.py
│   │   ├── options.py
│   │   ├── rss_news.py
│   │   └── sentiment.py
│   │
│   ├── config/
│   │   └── ticker_aliases.py
│   │
│   ├── processors/
│   │   ├── confidence_engine.py
│   │   ├── event_classifier.py
│   │   ├── indicators.py
│   │   ├── news_filter.py
│   │   ├── news_fusion.py
│   │   ├── screener.py
│   │   └── signal_fusion.py
│   │
│   ├── renderers/
│   │   ├── report.py
│   │   └── telegram.py
│   │
│   └── main.py
│
├── config/
│   └── watchlist.yaml
│
├── requirements.txt
└── README.md
```

---

# Intelligence Workflow

```text
Market Data Collection
        ↓
Macro Regime Evaluation
        ↓
Technical Screening
        ↓
Financial Context Enrichment
        ↓
News Intelligence Collection
        ↓
Signal Filtering
        ↓
Event Classification
        ↓
Confidence Governance
        ↓
AI Reasoning / Synthesis
        ↓
Report Rendering
        ↓
Automated Delivery
```

---

# Technology Stack

## Core

- Python 3.x

## Market Data

- yfinance
- Financial Modeling Prep (FMP)
- Finnhub
- RSS financial feeds

## AI

- Google Gemini API

## Delivery

- Telegram Bot API

## Libraries

- requests
- pandas
- python-dotenv
- feedparser
- urllib3

## Infrastructure

Developed and deployed on:

- Ubuntu Server
- Python virtual environments
- homelab infrastructure
- GitHub version control

---

# Setup

## Clone Repository

```bash
git clone https://github.com/dunga101/alphascope.git
cd alphascope
```

---

## Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment Variables

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

Run the full intelligence pipeline:

```bash
python -m app.main
```

---

# Roadmap

## Near-Term

- HTML email intelligence delivery
- richer executive summaries
- enhanced watchlist customization
- dashboard interface

## Intelligence Expansion

- FRED macroeconomic integration
- SEC EDGAR event intelligence
- richer analyst revision intelligence
- volatility structure analysis
- deeper options sentiment modeling

## Long-Term

- historical intelligence datastore
- regime comparison analytics
- signal calibration engine
- longitudinal market analytics
- ML-assisted experimentation

---

# Design Principles

AlphaScope follows strict engineering principles:

- deterministic preprocessing before AI reasoning
- modular separation of concerns
- signal over noise
- API cost discipline
- cache-aware architecture
- structured intelligence over speculation
- automation-first workflows
- maintainable engineering over hype scripting

---

# Disclaimer

AlphaScope is an engineering and educational project.

It does **not** provide investment advice.

No trade execution occurs.

Users remain fully responsible for their own financial decisions.

---

# Author

**Dulanga Mudalige**

Infrastructure | Cloud | Security | Automation | Systems Engineering

GitHub:
https://github.com/dunga101