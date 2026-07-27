# ADR-0001: Reference Architecture as Sprint 0 Implementation Prerequisite

## Status
Accepted (pending ratification of `docs/Architecture/REFERENCE_ARCHITECTURE.md`)

## Context
Implementation is beginning in Sprint 0. Approved business architecture exists, but a concise engineering baseline is required to prevent boundary and invariant violations during execution.

## Decision
Adopt `docs/Architecture/REFERENCE_ARCHITECTURE.md` as the minimum implementation-enabling architecture prerequisite.

## Rationale
- Preserves semantic/ownership integrity from approved architecture.
- Enables immediate coding without waiting for all future architecture phases.
- Prevents implementation-first drift.

## Consequences
### Positive
- Faster start with governance guardrails.
- Clear PR acceptance conditions.
- Lower early rework risk.

### Negative
- Requires stricter ADR/PR discipline from day one.

## Supersession
Supersedes any implicit “code-first then architect later” behavior.

## Review trigger
Revisit if a critical contradiction emerges between implementation constraints and approved architecture.