# TECHNICAL_DEBT

## Active Technical Debt Register (Frozen Baseline)

### TD-001: Executive Proof Snapshot per-chain dependency lookup pattern
- **Location:** `patches/post_model_sync/create_s2_f3_executive_proof_snapshot.py` (Jinja template body)
- **Type:** Performance optimization debt
- **Severity:** Non-blocking
- **Status:** Accepted / Deferred
- **Why deferred:** Current render scope is one approved attribution case at a time; observed behavior is acceptable for current data scale.
- **When to revisit:** If attribution chain sizes become materially larger or print rendering latency becomes a production concern.
- **Potential remediation direction (future, not implemented):** Pre-fetch dependency references once per render context and avoid per-row existence/doc fetch in loop.

## Exclusions
- Resolved defects are intentionally excluded from this file.
