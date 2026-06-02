# AlphaScope Architecture Decisions

Date: 2026-06-02

This document records the major architecture decisions behind AlphaScope
Investor Edition V1.

## Decision: Use PostgreSQL As The System Of Record

AlphaScope uses PostgreSQL for durable persistence of reports, technical
snapshots, fundamentals, FRED observations, macro snapshots, and investor
scores.

Rationale:

- The platform needs historical data, not only one-off reports.
- Investor scores and fundamentals need queryable history.
- PostgreSQL supports structured relational data and JSON fields where raw
  score details are useful.
- It is reliable for long-term self-hosted operation on `db-01`.

Tradeoff:

- PostgreSQL adds operational responsibility compared with flat files, but it
  enables historical analysis and future dashboard features.

## Decision: Use Cloudflare Pages For Dashboard Hosting

AlphaScope uses Cloudflare Pages to host the static web dashboard.

Rationale:

- The dashboard is static and JSON-driven.
- Cloudflare Pages provides simple, fast, globally cached hosting.
- No application server is required for V1 dashboard delivery.
- GitHub integration fits the existing repository workflow.

Tradeoff:

- Cloudflare project settings are external to the repository and must be
  validated through the dashboard.

## Decision: Use Git-Driven Deployment

AlphaScope deploys by pushing generated web data to `origin/web-launch`.
Cloudflare Pages deploys from that branch.

Rationale:

- Git provides an auditable deployment history.
- The automation can run without direct Cloudflare API credentials.
- Rollback is straightforward with Git revert.
- The deployment branch isolates generated production artifacts from feature
  branch development.

Tradeoff:

- Cloudflare must be configured to deploy the correct branch and output
  directory.

## Decision: Use Static Dashboard Generation

The V1 dashboard is generated as static HTML plus JSON artifacts under `web/`.

Rationale:

- Static hosting reduces runtime infrastructure complexity.
- The dashboard can be updated through generated JSON rather than a running web
  app server.
- Cloudflare Pages is a natural fit for static assets.
- Failure modes are simpler: stale JSON, failed deploy, or cache issues.

Tradeoff:

- Personalization, authenticated users, and dynamic portfolio features are
  deferred.

## Decision: Use FRED For Macro Intelligence

AlphaScope uses FRED for macroeconomic observations and derived macro regime
context.

Rationale:

- FRED is authoritative for U.S. macroeconomic series.
- Macro regime context improves investor interpretation beyond stock-level
  data.
- FRED observations can be persisted and reused for future trend analysis.

Tradeoff:

- Macro data updates at lower frequency than market data, so freshness
  expectations differ from quotes.

## Decision: Use FMP For Quotes, Profiles, And Fundamentals

AlphaScope uses Financial Modeling Prep for quote snapshots, company profiles,
and fundamental data.

Rationale:

- FMP provides structured fundamentals suitable for deterministic scoring.
- The investor scoring engine needs valuation, debt, ROE, free cash flow, and
  dividend fields.
- FMP outputs are practical for both persistence and dashboard export.

Tradeoff:

- API quota and cache behavior must be monitored before expanding the symbol
  universe.

## Decision: Use Finnhub And RSS For Market News

AlphaScope uses Finnhub and RSS feeds for event and headline context.

Rationale:

- Finnhub provides a market news API.
- RSS feeds add coverage from financial news sources.
- The combined event feed gives Gemini and the event processors broader
  context.

Tradeoff:

- News quality and availability vary by source, so event synthesis should be
  treated as interpretive.

## Decision: Use Gemini For AI-Assisted Synthesis

AlphaScope uses Gemini to synthesize market and event intelligence after data
collection.

Rationale:

- AI summaries make market context easier to consume.
- Deterministic scoring remains separate from AI interpretation.
- The pipeline can still produce structured data even if AI quality varies.

Tradeoff:

- Gemini outputs are not deterministic and should not be treated as the source
  of truth for investor scores.

## Decision: Use systemd For Scheduling

AlphaScope uses systemd timer/service units for unattended scheduled execution.

Rationale:

- systemd is native to the Ubuntu host.
- Timers provide durable scheduled execution with logs in journald.
- Service configuration clearly defines user, working directory, environment,
  timeout, and command.
- It is simpler than introducing a separate orchestration system for V1.

Tradeoff:

- Operations are host-specific and require Linux/systemd familiarity.

## Decision: Use Proxmox Infrastructure

AlphaScope runs in a Proxmox-backed environment with separate automation and
database roles.

Rationale:

- `automation-01` can own scheduled application execution and Git deployment.
- `db-01` can own PostgreSQL separately.
- Separation improves maintainability and operational clarity.
- Proxmox supports practical homelab and infrastructure engineering evidence.

Tradeoff:

- Infrastructure configuration lives outside the application repository and
  must be documented operationally.

