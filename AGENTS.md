# AlphaScope Agent Instructions

## Project Overview

AlphaScope is an AI-assisted market intelligence and investor research platform.

Current architecture:

- Python
- PostgreSQL
- Gemini AI
- Financial Modeling Prep (FMP)
- Telegram delivery
- Web dashboard

The system already collects:

- Technical indicators
- Company profiles
- News
- Market snapshots
- Intelligence reports

## Development Rules

- Do not remove existing functionality.
- Preserve backward compatibility.
- Prefer small focused commits.
- Use existing project structure.
- Reuse existing collectors and database models whenever possible.

## Database

Database server:

db-01

Database:

alphascope

Existing tables include:

- market_prices
- technical_snapshots
- company_profiles
- intelligence_reports
- fundamental_snapshots

## Goal

Build AlphaScope Investor Edition.

Required capabilities:

1. Persist fundamentals
2. Calculate investor scores
3. Rank opportunities
4. Display ranked opportunities in dashboard
5. Support dividend-oriented investing

## Deliverables

Before changing code:

Generate IMPLEMENTATION_PLAN.md

Do not modify code until plan is approved.
