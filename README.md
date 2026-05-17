# AlphaScope

AI-assisted market intelligence platform for structured market analysis.

AlphaScope ingests live market data, applies technical screening logic, uses LLM-based interpretation, and delivers market intelligence summaries via Telegram.

---

## Current Capabilities

### Market Data Ingestion
Collects live market data using Yahoo Finance.

Current inputs:
- ticker price history
- OHLC market data
- technical indicator source data

---

## Technical Analysis Engine

Current analysis includes:
- RSI evaluation
- moving average trend logic
- momentum screening
- candidate filtering

---

## AI Analysis Layer

Uses Gemini for contextual interpretation.

Responsibilities:
- interpret screened technical signals
- summarize findings
- generate market commentary

---

## Notification Delivery

Telegram bot integration for automated delivery.

Features:
- automated digest delivery
- direct alert notifications
- private reporting

---

## Technology Stack

### Core
- Python 3
- yfinance
- requests
- python-dotenv

### External Services
- Gemini API
- Telegram Bot API
- Yahoo Finance

### Development Environment
- Ubuntu Server
- VS Code Remote SSH
- Git / GitHub

---

## Current Project Structure

```text
alphascope/
├── README.md
├── app/
│   ├── ai_analyzer.py
│   ├── indicators.py
│   ├── main.py
│   ├── market_data.py
│   ├── notifier.py
│   ├── report_generator.py
│   ├── screener.py
│   └── test_gemini.py
│
├── requirements.txt
└── .gitignore
```

---

## AlphaScope v2 Roadmap

### Intelligence Improvements
- macro regime detection
- sector rotation analysis
- earnings awareness
- volume intelligence
- confidence scoring
- anomaly detection

### Architecture Refactor
Move from prototype layout to modular architecture:

```text
collectors/
processors/
ai/
renderers/
```

### Future Enhancements
- news sentiment ingestion
- market breadth metrics
- institutional sentiment
- backtesting
- performance analytics

---

## Design Philosophy

AlphaScope is being built as an engineering-first intelligence platform:

- modular
- observable
- deterministic where possible
- intelligence-focused
- no automated trade execution

This is a market intelligence system, not a trading bot.

---

## Status

Prototype complete.

Currently transitioning to AlphaScope v2.