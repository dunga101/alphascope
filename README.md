# AlphaScope 📈🧠

**AI-assisted stateful financial market intelligence platform engineered for resilient market analysis, structured signal governance, and disciplined decision-support workflows.**

AlphaScope is a modular Python-based intelligence system that transforms fragmented financial data into structured, interpretable market intelligence.

It combines deterministic market analytics, structured financial enrichment, event-aware intelligence pipelines, confidence governance, persistent historical memory, and AI-assisted reasoning to generate institutional-style daily intelligence briefings.

AlphaScope is not a trading bot.

It is an engineering-driven intelligence platform.

---

# Philosophy

Modern markets generate overwhelming quantities of data:

* macroeconomic signals
* price action
* volatility shifts
* earnings catalysts
* analyst revisions
* geopolitical events
* sector rotation
* bond market divergence
* sentiment noise
* financial headlines

Raw information is abundant.

Actionable intelligence is scarce.

AlphaScope exists to bridge that gap through disciplined engineering.

The platform is designed to:

* collect
* normalize
* enrich
* classify
* score
* synthesize
* persist
* evaluate

market intelligence using a layered, resilient architecture.

---

# Core Platform Capabilities

## Market Regime Intelligence

AlphaScope evaluates broad market conditions using macro proxies including:

* S&P 500 (^GSPC)
* Nasdaq 100 (^NDX)
* Dow Jones (^DJI)
* Russell 2000 (^RUT)
* VIX (^VIX)
* US 10Y Treasury Yield (^TNX)
* Gold
* Oil
* Bitcoin

This enables regime classification such as:

* Risk-On
* Neutral
* Risk-Off
* Strong Risk-Off

Outputs include:

* regime classification
* confidence scoring
* tactical bias interpretation
* macro context awareness
* systemic event detection

---

## Technical Screening Engine

Watchlist securities are analyzed using deterministic technical scoring models.

### Indicators

* RSI
* SMA20
* SMA50
* momentum structure
* volume participation
* trend confirmation

### Example Watchlist

* SPY
* QQQ
* NVDA
* MSFT
* AMD
* TSLA
* GOOGL
* META
* AMZN
* SHOP.TO

### Classification System

* HIGH CONVICTION
* WATCHLIST
* NEUTRAL
* WEAK
* AVOID

AlphaScope identifies:

* strong setups
* overheated conditions
* weak technical structures
* deteriorating participation
* regime-sensitive setups

---

## Sector Rotation Intelligence

ETF breadth monitoring tracks sector leadership:

* XLK
* XLF
* XLI
* XLY
* XLU
* XLRE
* XLC
* XLV
* XLP
* XLE

Used for:

* leadership detection
* defensive rotation awareness
* cyclical weakness identification
* participation analysis
* macro breadth interpretation

---

## Structured Financial Intelligence

AlphaScope integrates Financial Modeling Prep (FMP) data for:

* live quotes
* company profiles
* structured fundamentals
* valuation context
* company metadata
* financial statement enrichment

This improves contextual intelligence beyond pure technical analysis.

---

## Event Intelligence Pipeline

AlphaScope includes structured event-aware intelligence ingestion.

### Data Sources

* Finnhub financial news
* curated RSS financial feeds
* structured catalyst filtering

### Capabilities

* earnings event awareness
* analyst commentary ingestion
* headline relevance scoring
* ticker alias matching
* junk suppression
* crypto noise filtering
* clickbait rejection

Goal:

AI receives curated signal — not random internet noise.

---

## Confidence Governance Engine

AlphaScope separates:

* market regime confidence
* event-driven confidence
* weighted confidence fusion

This avoids simplistic “AI says buy” behavior and enforces deterministic governance before AI interpretation.

The arbitration engine supports:

* systemic event detection
* confidence disagreement penalties
* macro-first weighting
* confidence caps during instability

---

## AI Intelligence Layer

Google Gemini is used strictly as a reasoning layer.

### Responsibilities

* macro interpretation
* signal synthesis
* executive commentary generation
* risk identification
* contextual summarization
* decision-support narrative generation

AI operates **after deterministic preprocessing**.

This architecture intentionally prevents noisy raw prompting.

---

# Stateful Intelligence Memory

AlphaScope evolved from a stateless script into a resilient stateful intelligence platform.

The platform now persists structured historical intelligence into PostgreSQL.

## Intelligence Reports

Daily strategic intelligence snapshots:

`intelligence_reports`

Stores:

* market regime
* confidence
* executive summary
* tactical posture
* bullish signals
* bearish signals
* risk flags
* raw AI output

---

## Event Intelligence Memory

Daily event-aware intelligence persistence:

`event_snapshots`

Stores:

* event regime
* event confidence
* major headlines
* bullish events
* bearish events
* risk events
* raw event intelligence

---

## Technical Snapshot Persistence

AlphaScope now stores structured daily technical intelligence:

`technical_snapshots`

Per-symbol persistence includes:

* signal score
* trend score
* momentum score
* volatility score
* risk score
* technical regime
* technical confidence
* raw signal structure

This enables historical technical analysis across regimes.

---

# Resilient Execution Modes

## FULL MODE

Uses:

* FMP
* Gemini AI
* event intelligence
* fundamentals
* technical engine
* Telegram delivery
* persistence layer

Run:

```bash
python -m app.main full
```

---

## DEGRADED MODE

Used during API quota exhaustion or partial outages.

Disables:

* FMP quotes
* company profiles
* fundamentals

Preserves:

* macro analysis
* technical intelligence
* event intelligence
* Gemini reasoning
* Telegram delivery
* persistence layer

Run:

```bash
python -m app.main degraded
```

---

## OFFLINE MODE

Disaster survivability mode.

Disables:

* Gemini AI
* FMP enrichment

Uses deterministic fallback intelligence.

Run:

```bash
python -m app.main offline
```

---

# Automated Delivery

Current delivery:

✅ Telegram executive intelligence briefing

The platform now generates concise operational briefings rather than oversized report payloads.

---

# Engineering Highlights

AlphaScope demonstrates:

* modular Python architecture
* API integration engineering
* resilient execution design
* graceful degradation
* quota-aware API consumption
* confidence arbitration
* stateful persistence
* PostgreSQL integration
* structured intelligence pipelines
* deterministic preprocessing
* AI-assisted synthesis
* telemetry logging
* report rendering pipelines
* executive delivery systems
* historical cognition architecture
* environment-based secret management

---

# Architecture

```text
AlphaScope
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
Persistence Layer
        ↓
Executive Report Rendering
        ↓
Automated Delivery
```

---

# Technology Stack

## Core

* Python 3.x

## Market Data

* yfinance
* Financial Modeling Prep (FMP)
* Finnhub
* RSS financial feeds

## AI

* Google Gemini API

## Database

* PostgreSQL

## Delivery

* Telegram Bot API

## Libraries

* requests
* pandas
* psycopg2
* python-dotenv
* feedparser
* urllib3

---

# Infrastructure

Developed and operated on:

* Ubuntu Server
* Python virtual environments
* homelab infrastructure
* VS Code Remote SSH
* GitHub version control

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

DB_HOST=your_host
DB_NAME=alphascope
DB_USER=your_user
DB_PASSWORD=your_password
DB_PORT=5432
```

---

# Running AlphaScope

## Full Mode

```bash
python -m app.main full
```

## Degraded Mode

```bash
python -m app.main degraded
```

## Offline Mode

```bash
python -m app.main offline
```

---

# Roadmap

## Near-Term

* prediction outcome scoring
* confidence calibration engine
* historical regime analytics
* longitudinal signal validation
* enhanced executive summaries
* dashboard interface
* watchlist customization

## Intelligence Expansion

* FRED macroeconomic integration
* SEC EDGAR event intelligence
* richer analyst revision intelligence
* volatility structure analysis
* options sentiment expansion
* cross-asset correlation analysis

## Long-Term

* intelligence accuracy scoring
* AI confidence benchmarking
* probabilistic regime forecasting
* ML-assisted experimentation
* historical intelligence search engine
* multi-agent intelligence orchestration

---

# Design Principles

AlphaScope follows strict engineering principles:

* deterministic preprocessing before AI reasoning
* modular separation of concerns
* resilience over fragility
* signal over noise
* structured intelligence over speculation
* cache-aware architecture
* quota-aware API discipline
* graceful degradation
* automation-first workflows
* maintainable engineering over hype scripting

---

# Disclaimer

AlphaScope is an engineering and educational project.

It does not provide investment advice.

No trade execution occurs.

Users remain fully responsible for their own financial decisions.

---

# Author

**Dulanga Mudalige**

Infrastructure | Cloud | Security | Automation | Systems Engineering

GitHub:
[https://github.com/dunga101](https://github.com/dunga101)
