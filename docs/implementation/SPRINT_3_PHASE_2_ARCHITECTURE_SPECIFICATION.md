> **Status: Architecture Design Only**
>
> Sources constrained to approved Phase 1 documents:
> - `docs/implementation/SPRINT_3_PHASE_1_CAPABILITY_ASSESSMENT.md`
> - `docs/implementation/SPRINT_3_PHASE_1_INDEPENDENT_REVIEW.md`
> - `docs/implementation/SPRINT_3_PHASE_1_RECONCILED_DECISION.md`
>
> Baseline `v0.2.0-baseline` is immutable.
> No implementation is authorized by this specification.

# SPRINT_3_PHASE_2_ARCHITECTURE_SPECIFICATION

Date: 2026-07-29  
Scope: Sprint 3 Feature 1 architecture design (domain/interaction architecture only)

---

## 0) Architectural Intent

Design the architecture for **Executive Decision Follow-Through Management** as an additive capability that composes existing Sprint 1/Sprint 2 governance artifacts and signals, while preserving frozen baseline contracts.

---

## 1) Capability Boundaries

### 1.1 Bounded context

## Follow-Through Orchestration Context

Purpose: coordinate and evaluate execution follow-through signals across existing governance records without mutating existing baseline contracts.

### 1.2 Responsibilities

1. Identify follow-through items from existing governance artifacts.
2. Prioritize follow-through items by risk/impact/timeliness signals.
3. Track follow-through progression via capability-local lifecycle semantics.
4. Produce governance-safe outcome signals for executive/owner operations.
5. Preserve traceability from follow-through outputs back to authoritative baseline records.

### 1.3 Explicit out-of-scope

- Redefining any existing Sprint 1/Sprint 2 `approval_state` behavior.
- Changing role permissions on frozen entities.
- Changing approved-record immutability rules.
- Creating duplicate source-of-truth persistence for existing governance entities.
- Implementing runtime artifacts (DocTypes/controllers/workflows/reports/print formats/patches/tests/APIs).

### 1.4 Interactions with Sprint 1/Sprint 2 capabilities

- Uses `Lighthouse Workflow Charter` as cohort/governance context.
- Uses `Decision Record` as decision lifecycle anchor.
- Uses `Dependency Exception Record` as operational risk and blockage signal.
- Uses `Attribution Case` as outcome-confidence context.
- Uses `Operational Review View` and `Executive Proof Snapshot` as existing visibility surfaces that must not be duplicated in purpose.

---

## 2) Domain Model (Technology-agnostic)

> No Frappe mapping in this section.

### 2.1 Entities

1. **FollowThroughItem**
   - Represents one actionable follow-through concern linked to governance records.
   - Identity: follow-through item identifier.

2. **FollowThroughCycle**
   - Represents a bounded review cadence window for follow-through evaluation.
   - Identity: cycle identifier + time window.

3. **EscalationCase**
   - Represents escalation state for unresolved/high-risk follow-through items.
   - Identity: escalation identifier.

### 2.2 Value objects

1. **PriorityScore**
   - Composite value used for relative prioritization.
2. **EscalationCondition**
   - Encodes rule outcome that escalation criteria are met.
3. **ResolutionCheckpoint**
   - Defines a required completion checkpoint.
4. **OutcomeClosureEvidence**
   - Immutable reference set proving closure rationale.
5. **MeasurementWindow**
   - Time boundary for KPI calculation and comparison.

### 2.3 Aggregates

1. **FollowThroughItem Aggregate** (root: FollowThroughItem)
   - Contains checkpoint progress, escalation linkage, and closure evidence references.

2. **FollowThroughCycle Aggregate** (root: FollowThroughCycle)
   - Contains scoped set of item references and cycle-level status signals.

### 2.4 Relationships

- One FollowThroughCycle contains many FollowThroughItems (by reference).
- One FollowThroughItem may reference zero/one EscalationCase.
- One FollowThroughItem may reference many source artifacts (charter/decision/dependency/attribution) by identity.
- One FollowThroughItem may require many ResolutionCheckpoints.
- One closed FollowThroughItem must carry OutcomeClosureEvidence.

### 2.5 Invariants

1. Follow-through items must reference at least one authoritative baseline artifact.
2. Follow-through closure cannot occur without closure evidence references.
3. Priority scoring must be deterministic for same inputs within a measurement window.
4. Escalation cannot be cleared without explicit resolution checkpoint satisfaction.
5. Capability-local lifecycle state must not mutate baseline entity state semantics.

---

## 3) Domain Events, Commands, and Lifecycle Transitions

### 3.1 Commands (intent)

- IdentifyFollowThroughItem
- PrioritizeFollowThroughItem
- StartFollowThroughItem
- EscalateFollowThroughItem
- RecordResolutionCheckpoint
- ResolveFollowThroughItem
- CloseFollowThroughItem
- StartFollowThroughCycle
- CloseFollowThroughCycle

### 3.2 Domain events (facts)

- FollowThroughItemIdentified
- FollowThroughItemPrioritized
- FollowThroughItemStarted
- FollowThroughItemEscalated
- ResolutionCheckpointRecorded
- FollowThroughItemResolved
- FollowThroughItemClosed
- FollowThroughCycleStarted
- FollowThroughCycleClosed

### 3.3 Capability-local lifecycle transitions

Proposed lifecycle for FollowThroughItem:

`Identified -> Prioritized -> In Progress -> (Escalated optional) -> Resolved -> Closed`

Architecture constraint:
- This lifecycle is capability-local and must not be conflated with existing Sprint 1/Sprint 2 `approval_state` workflows.

---

## 4) Integration Analysis (Dependency-only)

### 4.1 Lighthouse Workflow Charter

- Dependency role: scope/governance anchor for follow-through cohorting.
- Integration concern: read-only contextual linkage.

### 4.2 Decision Record

- Dependency role: primary decision anchor and timeline reference.
- Integration concern: read-only lifecycle and ownership context.

### 4.3 Dependency Exception Record

- Dependency role: operational risk source for prioritization/escalation.
- Integration concern: read-only risk/status signals; avoid redefining dependency workflow semantics.

### 4.4 Attribution Case

- Dependency role: outcome-confidence context for closure quality.
- Integration concern: read-only attribution/evidence references.

---

## 5) Data Ownership Model

| Information | Authoritative owner | Read-only consumers | Derived information |
|---|---|---|---|
| Charter governance context | Lighthouse Workflow Charter | Follow-Through Orchestration Context | Cohort alignment signals |
| Decision lifecycle context | Decision Record | Follow-Through Orchestration Context | Follow-through urgency/timing context |
| Dependency risk context | Dependency Exception Record | Follow-Through Orchestration Context | Priority/escalation candidate signals |
| Attribution outcome context | Attribution Case | Follow-Through Orchestration Context | Closure confidence context |
| Follow-through item state | FollowThroughItem Aggregate | Executive Sponsor / Workflow Owner / Ops views | Prioritized action queue |
| Escalation state | EscalationCase | FollowThroughItem Aggregate + operational views | Escalation trend metrics |
| KPI measurement rules/window | Measurement governance policy (capability-level) | All reporting consumers | KPI scorecards and trend deltas |

Ownership rule:
- Baseline entities remain authoritative for their native data.
- Follow-through context may derive signals, but must not duplicate authoritative baseline source-of-truth semantics.

---

## 6) Baseline Impact Review

## Classification: **Partially additive (conditional)**

Rationale:
- Additive when architecture composes existing artifact signals with capability-local semantics.
- Baseline-changing if any frozen contract is mutated.

### Baseline Change interaction checkpoints

1. Changing baseline `approval_state` semantics/transitions.
2. Changing permissions on frozen entities.
3. Changing approved-record immutability behavior.
4. Introducing duplicate source-of-truth persistence that redefines baseline ownership.

If any checkpoint is activated during future design refinement, treat as **Baseline Change** and gate with ADR before implementation.

---

## 7) Quality Attributes

### Scalability
- Expected to scale via signal composition over existing records and cycle batching.
- Risk point: large cross-record prioritization sets.

### Maintainability
- Improved if follow-through semantics stay capability-local and baseline contracts remain untouched.
- Degrades if lifecycle logic leaks into baseline entities.

### Auditability
- Strong when each follow-through state and closure evidence is traceable to source artifacts and measurement windows.

### Extensibility
- High if priority, escalation, and checkpoint policies are isolated as capability-level rules.

### Performance
- Must avoid redundant re-derivation or duplicated visibility surfaces; leverage existing signal artifacts where possible.

### Operational complexity
- Medium: introduces orchestration semantics that require ownership clarity and cadence discipline.

---

## 8) Risk Register (Architecture Phase)

| Risk | Type | Rank | Mitigation |
|---|---|---|---|
| Scope drift into frozen workflow/permission semantics | Governance/Architecture | High | Enforce Baseline Change checkpoints and approval gates |
| Insufficient KPI quantification for objective decisions | Product/Measurement | High | Require baseline windows, thresholds, and formulas before implementation approval |
| Duplication with ORV/EPS purpose | Architecture/Operational | Medium-High | Define explicit non-duplication boundary and role of each visibility artifact |
| Adoption resistance from additional process | Product/Operational | Medium | Keep follow-through model outcome-focused with clear owner value |
| Lifecycle ambiguity between local states and baseline states | Architecture | Medium | Maintain strict semantic separation between follow-through lifecycle and baseline `approval_state` |
| Migration ambiguity if ownership boundaries blur | Migration/Governance | Medium | Preserve source-of-truth ownership model and avoid contract mutation |

---

## 9) ADR Checkpoint

## ADR status: **Not triggered at this architecture definition level**

Reason:
- Current architecture remains conditional-additive and does not require immediate mutation of frozen Sprint 1/Sprint 2 contracts.

### Decisions that would trigger ADR if chosen later

1. Any change to existing baseline workflow semantics (`approval_state` transitions).
2. Any permission-model change on frozen entities.
3. Any immutability-policy relaxation or redefinition.
4. Any duplicate source-of-truth persistence that alters baseline ownership.

---

## 10) Architecture Decision Summary

- The architecture for Sprint 3 Feature 1 is approved as **conditional-additive orchestration architecture**.
- Capability semantics are defined without changing baseline runtime contracts.
- No implementation path is authorized until KPI quantification gates and baseline-safe constraints remain satisfied.

No implementation plans, backlog decomposition, or code artifacts are included in this specification.
