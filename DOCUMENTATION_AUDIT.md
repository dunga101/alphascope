# AlphaScope Documentation Audit

Generated before any documentation files were moved or archived.

## Scope

Audited all root-level Markdown files:

- `README.md`
- `AGENTS.md`
- `IMPLEMENTATION_PLAN.md`
- `INVESTOR_DASHBOARD_REQUIREMENTS.md`
- `INVESTOR_EDITION_REQUIREMENTS.md`
- `INVESTOR_DASHBOARD_IMPLEMENTATION_PLAN_V2.md`
- `IMPLEMENTATION_NOTES.md`

## Findings

### `README.md`

Purpose: project overview and entrypoint.

Status: keep at repository root.

Notes:

- Describes platform purpose, architecture, features, stack, persistence, and development status.
- Needs links to the consolidated active Investor Dashboard document and archived historical docs.
- Contains broad product claims that overlap with requirements docs, but this overlap is acceptable because README is the public orientation document.

### `AGENTS.md`

Purpose: agent/development instructions.

Status: keep at repository root.

Notes:

- Contains operational instructions that should remain discoverable by coding agents.
- Overlaps conceptually with Investor Edition requirements but serves a different audience and should not be archived.

### `IMPLEMENTATION_PLAN.md`

Purpose: current Sprint 1 implementation plan.

Status: consolidate into `docs/INVESTOR_DASHBOARD_V2.md`, then archive original.

Overlaps:

- Duplicates Investor Edition goals from `INVESTOR_EDITION_REQUIREMENTS.md`.
- Duplicates dashboard scope from `INVESTOR_DASHBOARD_REQUIREMENTS.md`.
- Supersedes parts of `INVESTOR_DASHBOARD_IMPLEMENTATION_PLAN_V2.md`.

Notes:

- This is the most current Sprint 1 source and should be the primary input for the consolidated active document.

### `INVESTOR_DASHBOARD_REQUIREMENTS.md`

Purpose: older dashboard requirements.

Status: archive.

Overlaps:

- Dashboard homepage, opportunity detail view, score breakdown, fundamentals, and technical metrics overlap with the current Sprint 1 plan.
- Includes future requirements such as historical trend charts, Flask, and Chart.js that conflict with the current static-site preservation constraint.

Notes:

- Useful historical reference, but not an active source of truth.

### `INVESTOR_EDITION_REQUIREMENTS.md`

Purpose: earlier Investor Edition requirements.

Status: archive.

Overlaps:

- Fundamental persistence, scoring engine, ranking, dashboard fields, recommendation logic, and investor focus overlap with the current Sprint 1 plan.

Notes:

- Most requirements are now implemented or restated in the current Sprint 1 plan.
- Keep archived for traceability.

### `INVESTOR_DASHBOARD_IMPLEMENTATION_PLAN_V2.md`

Purpose: earlier broad dashboard implementation plan.

Status: archive.

Overlaps:

- Static site architecture, JSON contracts, dashboard layout, opportunity page, mobile behavior, and migration steps overlap with the current Sprint 1 plan.

Notes:

- Contains broader future architecture ideas that exceed Sprint 1, including per-symbol opportunity JSON, shared asset refactors, and structured full-report sections.
- Keep archived as historical planning context, not active scope.

### `IMPLEMENTATION_NOTES.md`

Purpose: Phase 2 implementation notes.

Status: archive.

Overlaps:

- Describes existing investor scoring, ranking, persistence, and pipeline integration already captured in current findings.

Notes:

- Historical record of previous implementation work.
- Not active requirements or planning.

## Consolidation Plan

Create:

- `docs/INVESTOR_DASHBOARD_V2.md`

This document will become the single active source for Sprint 1 Investor Dashboard requirements and implementation scope.

Move to:

- `docs/archive/IMPLEMENTATION_PLAN.md`
- `docs/archive/INVESTOR_DASHBOARD_REQUIREMENTS.md`
- `docs/archive/INVESTOR_EDITION_REQUIREMENTS.md`
- `docs/archive/INVESTOR_DASHBOARD_IMPLEMENTATION_PLAN_V2.md`
- `docs/archive/IMPLEMENTATION_NOTES.md`

Keep at root:

- `README.md`
- `AGENTS.md`
- `DOCUMENTATION_AUDIT.md`

## README Update Needed

Update `README.md` to link to:

- Active Sprint 1 document: `docs/INVESTOR_DASHBOARD_V2.md`
- Archived historical docs: `docs/archive/`

## No Deletions Recommended

No documentation should be deleted in this cleanup. Obsolete or superseded documents should be archived to preserve project history.
