# AlphaScope 📈🧠

**AI-powered daily market intelligence platform for retail investors, analysts, and market observers.**

AlphaScope combines live market data, technical analysis, macro sentiment detection, and AI-driven interpretation to generate actionable daily market intelligence reports.

---

## Overview

AlphaScope is a Python-based market intelligence engine designed to transform raw market data into concise, decision-ready insights.

Instead of manually checking multiple websites, indicators, and economic signals, AlphaScope automates:

* Market regime analysis
* Technical screening
* Sector rotation awareness
* Risk detection
* Earnings event monitoring
* AI-generated strategic commentary
* Automated delivery via Telegram (email distribution planned)

---

## Core Features

### Market Regime Intelligence

Evaluates overall market conditions using:

* S&P 500
* Nasdaq 100
* Dow Jones
* Russell 2000
* VIX
* US 10Y Treasury Yield

Detects:

* Risk-on
* Neutral
* Risk-off
* Strong risk-off

With confidence scoring and capital allocation bias guidance.

---

### Technical Stock Screening

Screens watchlist securities using technical indicators:

* RSI
* Moving averages
* Volume confirmation
* Momentum scoring

Current watchlist includes:

* SPY
* QQQ
* NVDA
* MSFT
* AMD
* TSLA
* GOOGL
* META
* SHOP
* AMZN

---

### Sector Rotation Analysis

Tracks ETF sector strength:

* XLK
* XLF
* XLI
* XLY
* XLU
* XLRE
* XLC
* XLV
* XLP

Identifies:

* Strong sectors
* Weak sectors
* Relative leadership changes

---

### Earnings Event Awareness

Flags upcoming high-impact earnings catalysts.

Examples:

* NVDA
* AAPL
* MSFT
* AMZN
* META
* TSLA

Helps avoid blind exposure into event risk.

---

### AI Market Commentary

Uses Google Gemini AI to interpret raw signals into actionable narrative intelligence.

Examples:

* Short-term outlook
* Medium-term outlook
* Major risk factors
* Opportunity themes
* Tactical positioning guidance

---

### Automated Delivery

Current delivery method:

✅ Telegram bot notifications

Planned:

* HTML email distribution
* subscriber lists
* scheduled daily reports

---

## Architecture

```text
AlphaScope
│
├── app/
│   ├── ai/
│   │   └── gemini_client.py
│   │
│   ├── collectors/
│   │   ├── advanced_breadth.py
│   │   ├── macro.py
│   │   └── earnings.py
│   │
│   ├── processors/
│   │   ├── indicators.py
│   │   ├── screener.py
│   │   └── regime.py
│   │
│   ├── renderers/
│   │   ├── report.py
│   │   └── telegram.py
│   │
│   └── main.py
│
├── .env
├── requirements.txt
└── README.md
```

---

## Technology Stack

**Language**

* Python 3.x

**Libraries**

* yfinance
* pandas
* requests
* python-dotenv

**AI**

* Google Gemini API

**Messaging**

* Telegram Bot API

**Infrastructure**

* Ubuntu Server
* Python virtual environment
* GitHub version control

---

## Example Workflow

```text
Market data collection
        ↓
Macro signal analysis
        ↓
Technical screening
        ↓
Regime scoring
        ↓
AI interpretation
        ↓
Report generation
        ↓
Telegram delivery
```

---

## Example Output

AlphaScope generates intelligence like:

* Market regime classification
* Composite risk score
* Technical ranking
* Overheated names
* Sector weakness
* Earnings event warnings
* Tactical AI commentary

---

## Setup

### Clone repo

```bash
git clone https://github.com/dunga101/alphascope.git
cd alphascope
```

---

### Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### Install dependencies

```bash
pip install -r requirements.txt
```

---

### Configure environment

Create:

```bash
.env
```

Example:

```env
GEMINI_API_KEY=your_key_here
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

## Run AlphaScope

Generate report:

```bash
python -m app.renderers.report
```

Run full pipeline:

```bash
python -m app.main
```

---

## Roadmap

### Near-term

* HTML email delivery
* subscriber distribution lists
* better visual report formatting
* scheduled daily execution

### Mid-term

* database-backed historical intelligence
* signal accuracy tracking
* portfolio watchlists
* customizable alerts

### Long-term

* web dashboard
* public AlphaScope portal
* multi-user subscriptions
* API access
* premium intelligence tiers

---

## Design Philosophy

AlphaScope was built around a simple principle:

> Raw market data is abundant. Actionable intelligence is rare.

The goal is not to produce noise.

The goal is to produce concise, strategic market awareness.

---

## Author

**Dulanga Mudalige**
Infrastructure | Cloud | Security | Automation

GitHub:
https://github.com/dunga101
