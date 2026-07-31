> **Status: Planning Only**
>
> Not implemented.
> Baseline `v0.2.0-baseline` is immutable.
> Any proposal that changes Sprint 1/Sprint 2 behavior is a **Baseline Change** and requires ADR approval before implementation.

# SPRINT_3_PHASE_1_CAPABILITY_ASSESSMENT

Date: 2026-07-29  
Scope: Sprint 3 Phase 1 planning (capability assessment only)

---

## Purpose

Identify the highest-value business capability to implement next after the frozen Sprint 2 baseline.

---

## Baseline Context (Evidence)

- Sprint 1 + Sprint 2 deliver governed records, sponsor-gated workflows, register reports, `Operational Review View`, and `Executive Proof Snapshot`.
- Baseline runtime and release readiness are already validated for `v0.2.0-baseline`.
- No Sprint 3 implementation is authorized in this phase.

---

## Candidate Capability Assessment

### Candidate A — Executive Decision Follow-Through Management

**Business problem**  
Cross-record execution follow-through is still manual and fragmented after governance capture/approval.

**Expected customer value**  
- Faster sponsor/owner action on high-risk items
- Lower decision-to-resolution latency
- Reduced manual reconciliation effort
- Better executive confidence in accountability

**Success metrics / KPIs**  
1. Decision follow-through latency (decrease)  
2. Manual reconciliation effort hours (decrease)  
3. Governance adherence rate across transitions (increase)  
4. Sponsor confidence score (increase)  
5. Adoption rate by eligible sponsor/owner cohort (increase)

**Additive vs Baseline Change**  
- Current planning assumption: **Additive**  
- **Baseline Change trigger:** if scope requires changes to existing `approval_state` semantics, role permissions, immutability rules, or duplicate persistence behavior.

**Dependencies**  
- Existing baseline records: Charter, Decision, Dependency, Attribution  
- Existing visibility artifacts: Operational Review View, Executive Proof Snapshot  
- KPI measurement inputs and agreed telemetry windows

**Risks**  
- KPI baselines not yet quantified  
- Potential scope creep into baseline contract modifications  
- Misalignment on prioritization without comparative scoring evidence

---

### Candidate B — Baseline KPI Instrumentation & Measurement Governance

**Business problem**  
Outcome measurement definitions are directional, but not yet fully quantified for objective go/no-go decisions.

**Expected customer value**  
- Higher decision confidence in release/priority gates
- Reduced debate over success criteria
- Better auditability of business impact

**Success metrics / KPIs**  
1. % KPIs with approved baseline values (increase to full coverage)  
2. % KPI definitions with approved target thresholds (increase)  
3. Reporting cadence adherence (increase)

**Additive vs Baseline Change**  
- Planning assumption: **Additive**  
- **Baseline Change trigger:** none expected unless existing frozen semantics are redefined.

**Dependencies**  
- Sponsor/owner agreement on KPI windows and thresholds  
- Data source reliability

**Risks**  
- May improve governance clarity without directly improving operational follow-through by itself

---

### Candidate C — Executive Readout Consolidation (Planning-level)

**Business problem**  
Leadership signals are spread across existing artifacts and may require manual synthesis.

**Expected customer value**  
- Faster executive review preparation
- Improved consistency of leadership updates

**Success metrics / KPIs**  
1. Executive review preparation time (decrease)  
2. Signal completeness across required domains (increase)

**Additive vs Baseline Change**  
- Planning assumption: **Additive**  
- **Baseline Change trigger:** if implementation attempts to alter existing report/print contract behavior.

**Dependencies**  
- Existing report/print outputs and governance records

**Risks**  
- Risk of duplicating existing `Operational Review View` / `Executive Proof Snapshot` purpose if poorly scoped

---

## Prioritization Outcome

### Highest-Value Capability Recommendation

## **Executive Decision Follow-Through Management** (Candidate A)

### Why this is highest value now

1. It directly targets the largest remaining gap between governance capture and execution outcomes.
2. It operationalizes value from already-implemented Sprint 1/Sprint 2 artifacts.
3. It has stronger near-term customer impact potential than measurement-only or readout-only options.

---

## Baseline Compatibility Decision

- **Recommended path:** pursue Candidate A as **additive-first** planning scope.
- **Baseline Change policy:** any requirement that modifies Sprint 1/Sprint 2 behavior must be explicitly tagged **Baseline Change** and blocked pending ADR approval before implementation.

---

## Dependencies, Risks, and Controls for Recommended Capability

### Dependencies
- Approved KPI baseline windows and target thresholds
- Sponsor and workflow-owner operating cadence agreement
- Explicit non-duplication boundary versus existing ORV/EPS artifacts

### Risks
- Quantitative KPI uncertainty before pilot baselining
- Scope drift into frozen workflow/permission contracts
- Ambiguity in action ownership across roles

### Controls
- Additive-only planning gate
- Explicit Baseline Change tagging rule
- ADR trigger checklist for any contract-altering requirement

---

## Final Recommendation

Proceed with Sprint 3 Phase 1 planning centered on:

1. **Executive Decision Follow-Through Management** as primary capability,
2. KPI baseline quantification and target-setting as pre-implementation gate,
3. strict additive-first boundaries, with mandatory ADR for any Baseline Change.

No implementation work is authorized by this document.
