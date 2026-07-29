# SPRINT_3_PLANNING_BRIEF

Date: 2026-07-29  
Status: Planning only (no implementation authorized)

---

## 1) Executive Summary

### Sprint objective
**[Recommendation]** Define and validate a new business capability: **Executive Decision Follow-Through Management**.

### Target business capability
**[Recommendation]** Give sponsors and workflow owners a single, outcome-oriented operating capability to detect, prioritize, and resolve high-risk decision follow-through gaps before they become expensive reversals or delays.

### Expected business outcome
**[Recommendation]** Faster sponsor action on critical items, lower approval/dependency cycle delays, and measurable reduction in manual reconciliation effort across charter → decision → dependency → attribution governance flow.

### Why this capability is the highest priority
**[Fact]** Sprint 1 + Sprint 2 already established governed records, approval workflows, operational visibility, and executive proof output.  
**[Recommendation]** The next highest-value step is operationalizing these foundations into a business capability that improves decision execution outcomes (not adding another isolated technical artifact).

---

## 2) Product Prioritization Justification

### Why should this capability be built now?
**[Fact]** Baseline now includes end-to-end governance primitives (records, workflows, reports, proof snapshot).  
**[Recommendation]** Building follow-through capability now converts those primitives into direct business outcomes (latency reduction and governance consistency) while adoption momentum is high.

### What measurable business problem does it solve?
**[Recommendation]** It addresses delayed sponsor actions, fragmented follow-up, and manual cross-record tracking that increases execution risk and decision-to-outcome lag.

### Why is it more valuable than the next three candidate capabilities?
**[Recommendation]**
1. It directly affects core outcome metrics (decision latency, governance adherence, confidence).  
2. It activates value from already-implemented Sprint 1 + 2 assets.  
3. It has lower change risk than introducing entirely new domains.

### What happens if this sprint is delayed?
**[Recommendation]**
- Existing governance artifacts remain under-leveraged.
- Manual coordination cost persists.
- Confidence in decision-to-outcome accountability improves slower than target.

---

## 3) Problem Definition

### Current operational problem
**[Recommendation]** Teams can capture and approve governance records, but cross-record follow-through still requires manual synthesis and proactive escalation by individuals.

### Target users
**[Fact]** Current baseline roles: `EIP Executive Sponsor`, `EIP Workflow Owner`, `EIP Operations Manager`, `System Manager`.  
**[Recommendation]** Primary users for this capability: Executive Sponsor + Workflow Owner; secondary: Operations Manager.

### Existing workflow
**[Fact]**
- Charter, Decision, Dependency, Attribution each follow governed approval-state lifecycle.
- `Operational Review View` provides dependency-centric operational visibility.
- `Executive Proof Snapshot` provides approved attribution evidence narrative.

### Pain points
**[Recommendation]**
- Cross-object prioritization still manual.
- Sponsor action timing is not managed as a dedicated business capability.
- Operational risk can remain visible but not action-orchestrated.

### Current workarounds
**[Recommendation]**
- Manual report exports
- Ad hoc status meetings
- Spreadsheet-level follow-up lists

### Why Sprint 1 and Sprint 2 do not already solve this problem
**[Fact]** Sprint 1 + 2 implemented governance capture/approval, register visibility, operational review, and proof rendering.  
**[Fact]** They do not yet define a distinct business capability for systematic follow-through orchestration and measurable action-cycle improvement.

---

## 4) Business Value Assessment

> **Important:** Baseline absolute values must be confirmed from production telemetry before commitment.

### KPI Framework

| KPI | Definition | Baseline Source | Target Direction |
|---|---|---|---|
| ROI proxy | Estimated labor + delay cost avoided from faster follow-through | Ops time logs + cycle timing | Increase |
| Decision latency | Time from decision submission/approval to stable downstream resolution state | Record timestamps | Decrease |
| Manual effort reduction | Hours spent on manual cross-record reconciliation | Ops self-report + audit sampling | Decrease |
| Governance improvement | % records meeting policy-complete transitions without rework | Workflow + validation outcomes | Increase |
| Executive confidence | Sponsor-reported confidence score in decision accountability | Structured sponsor survey | Increase |
| Adoption | % eligible workflows/users actively using Sprint 3 capability | Usage telemetry | Increase |

### Value Hypothesis
**[Recommendation]** If sponsors and owners can act on prioritized follow-through signals in one operating loop, then latency and manual effort decline while governance quality and executive confidence improve.

---

## 5) Capability Definition

> Implementation intentionally excluded.

### Users
- Executive Sponsor
- Workflow Owner
- Operations Manager
- System Manager (oversight)

### Inputs
**[Fact]** Existing baseline records and states:
- Lighthouse Workflow Charter
- Decision Record
- Dependency Exception Record
- Attribution Case
- Operational Review View signals
- Executive Proof Snapshot output context

### Outputs
**[Recommendation]**
- Prioritized follow-through actions
- Governance-aligned action status view
- Measurable cycle/outcome metrics for leadership review

### Business rules
**[Recommendation]**
- Must respect existing role model and approval authority.
- Must not bypass or weaken current workflow invariants.
- Must preserve single source of truth in existing domain records.

### Success conditions
**[Recommendation]**
- Reduced decision follow-through latency.
- Lower manual reconciliation burden.
- Improved governance adherence and sponsor confidence.

### Failure conditions
**[Recommendation]**
- No measurable KPI movement.
- New process overhead without outcome gain.
- Any regression to frozen baseline contracts.

---

## 6) ADR Trigger Assessment

### Assessment outcome
**[Recommendation]** Current planning assumption: capability can be **additive** and likely **extends existing components** (especially operational visibility + governance usage patterns) without modifying frozen contracts.

### Baseline modification required?
**[Fact]** Not yet proven at planning stage.  
**[Recommendation]** During architecture review, if any requirement demands changing existing validation/workflow/permission contracts, raise ADR and pause implementation planning until approved.

### ADR trigger conditions (explicit)
Create ADR if Sprint 3 requires any of the following:
1. Changes to existing state-machine semantics
2. Relaxation of current immutability/approval controls
3. Re-definition of role permissions on frozen entities
4. New persistence that duplicates existing source-of-truth semantics

---

## 7) Domain Impact Analysis

| Existing baseline component | Affected? | Unchanged? | Extended? | Why |
|---|---:|---:|---:|---|
| Lighthouse Workflow Charter | Low | Yes | Potentially | Remains foundational governance source; may be referenced but should not be modified in baseline contract. |
| Decision Record | Medium | Yes | Potentially | Central decision lifecycle anchor for follow-through measurement. |
| Dependency Exception Record | High | No | Potentially | Primary operational risk signal source in current baseline. |
| Attribution Case | Medium | Yes | Potentially | Outcome attribution and confidence context for completion quality. |
| Operational Review View | High | No | Potentially | Existing operational signal surface likely leveraged/extended conceptually for follow-through capability. |
| Executive Proof Snapshot | Low | Yes | Potentially | Executive evidence artifact; may inform confidence narratives but should remain baseline-safe. |

> **Interpretation note:** “Potentially extended” here means *business-capability usage or additive layering*, not approved code changes.

---

## 8) Functional Requirements

## Must Have
1. Define a measurable sponsor/owner follow-through operating loop tied to existing governance records.
2. Provide clear prioritization criteria for high-risk/high-impact follow-through items.
3. Preserve current authority model (owner/sponsor/system manager boundaries).
4. Produce KPI-ready outputs for leadership review.

## Should Have
1. Explicit mapping from follow-through states to measurable outcome checkpoints.
2. Clear accountability ownership for each action class.
3. Repeatable periodic review cadence definition.

## Could Have
1. Segmented views by charter/decision criticality.
2. Confidence trend views aligned with attribution outcomes.
3. Pilot cohort comparison metrics.

## Out of Scope
1. Sprint 3 code implementation details.
2. New domain not anchored to current governance flow.
3. Any frozen baseline contract changes without ADR.

---

## 9) Non-Functional Requirements

### Security
- Must preserve existing role boundaries and access controls.

### Permissions
- Must not introduce privilege escalation paths relative to frozen baseline.

### Performance
- Must define acceptable response/analysis latency targets before implementation.

### Scalability
- Must include scaling assumptions for number of decisions/dependencies under active follow-through.

### Auditability
- Must support traceable rationale for prioritization and action outcomes.

### Migration
- Planning outputs must specify whether additive migrations are needed and confirm no baseline-breaking changes.

### Maintainability
- Capability design must favor existing patterns (controller/workflow/report/print boundaries) and low coupling.

### Testing
- Must define measurable test obligations aligned to functional and KPI acceptance criteria before coding starts.

---

## 10) Acceptance Criteria

> Each criterion is measurable and implementation-agnostic.

1. **Capability definition completeness**  
   - Pass condition: all required sections in this brief are approved by product + architecture stakeholders.

2. **KPI measurability**  
   - Pass condition: for each KPI in Section 4, baseline source and target direction are approved.

3. **Governance compatibility**  
   - Pass condition: architecture review confirms no baseline contract regressions.

4. **ADR decision clarity**  
   - Pass condition: additive path confirmed or ADR opened and approved before implementation planning continues.

5. **Risk readiness**  
   - Pass condition: top risks have agreed mitigations and owners.

6. **Readiness gate completion**  
   - Pass condition: all items in Section 13 are approved.

---

## 11) Risk Register

| Risk | Probability | Impact | Mitigation | Owner |
|---|---|---|---|---|
| Capability chosen does not move KPI outcomes materially | Medium | High | Validate KPI baselines and pilot targets before implementation | Product Lead |
| Hidden dependency on frozen workflow semantics requires baseline change | Medium | High | ADR trigger review before any implementation design finalization | Architecture Owner |
| Manual process variance makes KPI measurement noisy | High | Medium | Define strict measurement windows and data definitions | Operations Manager |
| Scope creep into technical feature work without business validation | Medium | High | Enforce planning gate + signed acceptance criteria | Program Manager |
| Performance trade-offs in future additive surfaces | Low | Medium | Include performance budgets in NFR gate | Engineering Lead |
| Stakeholder misalignment on priority/capability definition | Medium | High | Formal sign-off meeting before backlog creation | Product Sponsor |

---

## 12) Dependency Analysis

### Internal dependencies

**[Fact]** Existing baseline internal components:
- **DocTypes:** Charter, Decision, Dependency, Attribution (+ child tables)
- **Workflows:** 4 approval workflows
- **Reports:** 4 register reports + Operational Review View
- **Print formats:** Executive Proof Snapshot
- **Patches:** S1/S2 post-model-sync provisioning chain

**[Recommendation]** Sprint 3 planning must explicitly map capability inputs/outputs to these existing components before proposing any additions.

### External dependencies

**[Fact]**
- Frappe framework runtime and workflow engine
- ERPNext/bench deployment environment
- Environment-specific monkey patches may affect workflow behavior in tests

**[Recommendation]** Validate external environment consistency for KPI data capture and governance behavior before pilot rollout.

---

## 13) Sprint Readiness Checklist

- [ ] **Business approval:** capability and value hypothesis approved
- [ ] **Architecture approval:** additive path confirmed or ADR approved
- [ ] **Security approval:** permission model impact reviewed
- [ ] **Data model approval:** source-of-truth boundaries confirmed
- [ ] **Workflow approval:** no baseline contract regression
- [ ] **Testing approval:** measurable test obligations defined
- [ ] **Migration approval:** migration strategy validated as additive/safe
- [ ] **KPI approval:** baseline definitions + target directions signed off

---

## 14) Sprint Exit Criteria

Sprint 3 can be considered freezable only when all are true:
1. Business capability outcomes are measured against approved KPI definitions.
2. No unresolved blocking defects exist.
3. Quality and regression gates pass without violating frozen baseline contracts.
4. Any required ADRs are approved and implemented as documented.
5. Release recommendation is formally approved with evidence.

---

## Fact vs Recommendation Legend

- **[Fact]** = Observed/implemented in frozen Sprint 1 + Sprint 2 baseline.
- **[Recommendation]** = Planning proposal requiring stakeholder agreement.

---

## Open Questions (must be resolved before implementation)

1. What is the exact business owner-approved KPI baseline window (e.g., last 30/60/90 days)?
2. Which single KPI is the primary Sprint 3 success KPI (north-star) for go/no-go?
3. What is the acceptable maximum decision follow-through latency target for pilot?
4. Which user cohort is the initial pilot population (by workflow count/team/business unit)?
5. Do stakeholders accept additive-only scope, or is a baseline-modifying change already anticipated?
6. If baseline modification is anticipated, which specific contract is affected and should ADR be opened now?
7. What minimum governance improvement threshold is required to call Sprint 3 successful?
8. What adoption threshold defines success for Executive Sponsor and Workflow Owner usage?
9. What reporting cadence is required for steering review (weekly/biweekly/monthly)?
10. Which risks from Section 11 are considered non-negotiable release blockers?
