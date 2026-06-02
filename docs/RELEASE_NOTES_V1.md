# AlphaScope Investor Edition V1 Release Notes

Release date: 2026-06-02

## Release Summary

AlphaScope Investor Edition V1 is an operational production release. It
combines market collection, macro intelligence, technical analysis, fundamental
analysis, investor scoring, PostgreSQL persistence, Telegram delivery, and a
Cloudflare-hosted static dashboard.

## Major Features

- Investor dashboard generated from static HTML and JSON artifacts.
- Ranked opportunity list with buy scores and recommendations.
- Investor scoring engine with valuation, financial quality, dividend, price
  position, and technical score components.
- Fundamental data collection and persistence.
- FRED macro intelligence and macro snapshot persistence.
- AI-assisted market and event synthesis through Gemini.
- Telegram daily brief delivery.
- Data health export for dashboard readiness validation.

## Architecture Highlights

- Python pipeline centered on `app/main.py`.
- PostgreSQL persistence for historical intelligence and investor data.
- Static dashboard under `web/`.
- Generated JSON exports under `web/data/`.
- Deterministic investor scoring separated from AI narrative synthesis.
- Proxmox-hosted operational model with `automation-01` and `db-01`.

## Operational Improvements

- systemd timer/service supports unattended production runs.
- Production runs validate generated JSON before deployment.
- Telegram summaries are sent after successful pipeline execution.
- Logs are available through journald and `logs/alphascope_refresh.log`.
- Operational troubleshooting is documented in `docs/OPERATIONS.md`.

## Deployment Improvements

- GitHub deploy-key issue remediated.
- Automated Git push validated.
- Deployment branch isolated as `web-launch`.
- Cloudflare Pages deployment validated.
- Production site update path confirmed.
- Browser cache issue identified and resolved during validation.

## Known Limitations

- Cloudflare Pages configuration remains external to the repository.
- Browser caching may temporarily obscure successful deployments.
- API quotas and third-party availability can affect data completeness.
- The dashboard is static and does not provide authenticated portfolio views.
- Historical trend visualizations are deferred.
- Gemini summaries are interpretive and not deterministic scoring inputs.

## Future Direction

- Add screenshot evidence for dashboard, Telegram, and Cloudflare deployments.
- Add generated-data freshness monitoring.
- Add historical score trend charts.
- Add API usage and quota observability.
- Add opportunity alerts and ranking-change notifications.
- Add portfolio-aware analysis.
- Expand the symbol universe gradually after runtime and quota validation.

