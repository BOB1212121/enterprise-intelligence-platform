# ARCHITECTURAL_DECISIONS

This file records implemented architecture decisions for the frozen Sprint 1 + Sprint 2 baseline.

## AD-001: Frappe-native workflow governance
- **Decision:** Use native Frappe Workflow + controller `validate()` as primary governance mechanism.
- **Why:** Strong platform alignment, low operational complexity, auditable state transitions.
- **Status:** Implemented.

## AD-002: Docstatus remains 0 across workflow states
- **Decision:** Keep state progression in custom `approval_state` rather than docstatus transitions.
- **Why:** Matches current implementation strategy and patch model in this codebase.
- **Status:** Implemented.

## AD-003: Idempotent post-model-sync patch provisioning
- **Decision:** Provision roles, workflow states/actions/workflows, and print format via post-model-sync patches.
- **Why:** Deterministic deploy/migrate behavior across sites.
- **Status:** Implemented.

## AD-004: Register visibility via Report Builder + one Script Report
- **Decision:** Use Report Builder for entity registers and Script Report only where computed visibility is required.
- **Why:** Minimize custom report code while supporting operational derived metrics.
- **Status:** Implemented (`Operational Review View` as Script Report).

## AD-005: Executive proof as print format, not persisted snapshot entity
- **Decision:** Implement `Executive Proof Snapshot` as Print Format on `Attribution Case`.
- **Why:** Avoid duplicate source of truth and additional schema/workflow complexity.
- **Status:** Implemented.

## AD-006: Server-side checkbox normalization for attribution evidence support flag
- **Decision:** Normalize `supports_claim` in controller validation.
- **Why:** Ensure runtime compatibility for accepted representations (`0/1`, booleans, numeric strings) and prevent serialization-edge regressions.
- **Status:** Implemented.

## Deferred (explicit)
- Print format performs per-chain-row dependency lookups. This is accepted for current scale and deferred for optimization until chain sizes are materially larger.
