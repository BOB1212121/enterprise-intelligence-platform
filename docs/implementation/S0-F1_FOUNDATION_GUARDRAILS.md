# S0-F1 Foundation Guardrails (Frappe-first)

## Purpose
Establish the minimum implementation guardrails required before Sprint feature delivery while preserving the existing Frappe app structure.

## Scope included
- Minimal bounded-context namespace scaffold (`bounded_contexts/`).
- Minimal test baseline for import and metadata validation.
- Minimal CI workflow for lint, import validation, and tests.

## Scope explicitly excluded
- No DocTypes
- No database schema changes
- No APIs
- No business services
- No AI logic
- No workflows

## Canonical architecture source
Architecture authority is `docs/MASTER_ARCHITECTURE.md`.

## Incremental delivery rule
Bounded-context subpackages are created only when the corresponding Sprint work starts.
