# EXTENSION_GUIDE

## Extension Boundary in Frozen Baseline

This baseline intentionally minimizes extension surface:

- No custom REST APIs
- No hook-driven orchestration for business invariants
- No background job extension points
- No alternate persistence for snapshot rendering

## Approved Extension Patterns

1. **Additive DocType/report/print artifacts**
2. **Controller `validate()` rules** for server-side invariants
3. **Idempotent post-model-sync patch provisioning**
4. **Role-consistent permission model reuse**

## Extension Safety Rules

- Must preserve Sprint 1 + Sprint 2 contracts
- Must be backward-compatible
- Must include tests + migration verification
- Must not bypass permission checks

## Existing extension-like implemented points

- Script Report (`Operational Review View`) for computed operational visibility
- Print Format (`Executive Proof Snapshot`) for approved attribution rendering

## Deferred

- No plugin framework has been implemented in Sprint 1 + Sprint 2.
