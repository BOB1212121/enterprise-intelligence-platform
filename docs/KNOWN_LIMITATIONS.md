# KNOWN_LIMITATIONS

This document lists **implemented baseline limitations** that are currently accepted.

## 1) Workflow monkey-patch environment variability
- Some tests conditionally skip native workflow transition checks when environment-level workflow monkey patches are detected.
- Impact: Native `apply_workflow` regression checks may be skipped in certain environments.
- Mitigation: Core validation remains enforced in controllers and workflow definitions.

## 2) Executive Proof Snapshot lookup pattern
- Print rendering performs per-chain-row dependency lookups in template execution.
- Impact: Additional database work proportional to chain-row count.
- Mitigation: Accepted for current scale and single-document render flow.

## 3) No persisted snapshot archival entity
- Executive proof is rendered from live approved `Attribution Case` data and linked records.
- Impact: No separate immutable snapshot object in baseline.
- Mitigation: Approved-record immutability controls remain in place for non-System Managers.

## 4) Scope boundary
- Baseline does not include Sprint 3+ capabilities.
- Impact: Any requested advanced capability must be planned as additive work after approval.
