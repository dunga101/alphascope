# AlphaScope Investor Dashboard Requirements

## Objective

Create the first production-ready AlphaScope Investor Dashboard.

The dashboard must transform AlphaScope from a backend intelligence platform into a usable investor-facing application.

Primary audience:

* Retail investors
* Long-term investors
* Dividend investors
* Family investment users

The dashboard should prioritize clarity and decision support over complexity.

---

# Dashboard Home Page

## Top Investment Opportunities

Display ranked opportunities sorted by Buy Score descending.

Columns:

* Symbol
* Company Name
* Buy Score
* Recommendation
* PE Ratio
* ROE
* Dividend Yield
* Distance from 52 Week Low
* Last Updated

---

## Market Summary

Display:

* Market Regime
* Regime Confidence
* Executive Summary
* Bullish Signals
* Bearish Signals
* Risk Flags

Source:

intelligence_reports table

---

## Opportunity Detail View

Clicking a symbol should show:

### Overview

* Symbol
* Company Name
* Recommendation
* Buy Score

### Score Breakdown

* Valuation Score
* Financial Quality Score
* Dividend Score
* Technical Score
* Price Position Score

### Fundamentals

* PE Ratio
* ROE
* Debt to Equity
* Free Cash Flow
* Dividend Yield

### Technical Metrics

* RSI
* SMA20
* SMA50
* SMA200
* ATR
* Volatility

---

## Historical Trend Section

Display charts for:

* Buy Score History
* Recommendation History
* Technical Score History

Data source:

investor_scores

---

# Technical Requirements

Backend:

* Python
* Existing PostgreSQL database

Frontend:

* Simple and maintainable
* Responsive
* Professional appearance

Preferred Framework:

* Flask

Visualization:

* Chart.js

---

# Design Goals

* Fast loading
* Investor-friendly
* Minimalist
* Professional
* Mobile-friendly
* Easy to extend

---

# Future Expansion

Planned future features:

* Opportunity alerts
* Portfolio tracking
* Watchlists
* Prediction accuracy tracking
* Dividend analytics
* Family investment portal
