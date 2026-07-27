# Enterprise Behaviour Graph (EBG)
## Conceptual Knowledge Model for the Operating System of Organisational Intelligence

**Scope:** Conceptual model only (no software, no database design, no AI model design).  
**Purpose:** Represent how an enterprise thinks, decides, acts, learns, and changes over time.

---

## 1) Design intent

The Enterprise Behaviour Graph is a living map of:
- **intent** (what the organization is trying to achieve),
- **power and incentives** (who benefits/loses),
- **decisions and actions** (what is chosen and done),
- **outcomes and consequences** (what happened),
- **learning and memory** (what is retained and reused),
- **adaptation over years** (how behavior evolves).

It treats the company as a socio-economic system, not a technical workflow.

---

## 2) Core modelling principles

1. **Behavior over artifacts** — model commitments and actions, not just documents.  
2. **Accountability over activity** — who decided what, under which assumptions.  
3. **Confidence is dynamic** — beliefs strengthen or decay with evidence.  
4. **Memory is compounding** — repeated patterns become institutional doctrine.  
5. **Power is explicit** — incentives and conflicts are first-class entities.  
6. **Time matters** — every entity has lifecycle, revision history, and context windows.

---

## 3) Entity universe (what exists)

Below is the conceptual entity set (including your examples), grouped into layers.

### A) Intent layer
- **Goal** — desired state/outcome (strategic or operational).
- **KPI** — measurable proxy for progress toward a goal.
- **Constraint** — boundary condition that limits feasible options.
- **Trade-off** — explicit compromise between competing goals/KPIs.

### B) Human and structure layer
- **Employee** — individual actor.
- **Manager** — employee with authority delegation and resource control.
- **Department** — formal organizational unit.
- **Role** — function-specific responsibility set (independent of person).
- **Incentive** — reward/penalty mechanism attached to roles or people.

### C) Decision layer
- **Decision** — committed choice among options.
- **Assumption** — belief used to justify a decision before full evidence exists.
- **Approval** — formal or informal authorization event.
- **Dependency** — prerequisite relation between decisions/actions/workstreams.

### D) Coordination layer
- **Meeting** — coordination episode where information is exchanged and commitments are created/modified.
- **Conflict** — incompatible objectives, interpretations, incentives, or resource claims.
- **Exception** — temporary override of normal policy/process/constraint.

### E) Governance layer
- **Policy** — durable rule that shapes allowable behavior.
- **Risk** — uncertain event or condition with impact on goals/KPIs.
- **Control** (optional extension) — mechanism intended to reduce risk likelihood/impact.

### F) Execution layer
- **Action** — concrete intervention taken by an accountable actor.
- **Outcome** — observed consequence of one or more actions.
- **Event** (optional extension) — meaningful change/state transition in the enterprise context.

### G) Intelligence layer
- **Knowledge** — validated reusable understanding (fact, pattern, causal claim, playbook).
- **Narrative** (optional extension) — shared interpretation that drives behavior beyond formal rules.
- **Capability** (optional extension) — repeatable competence to execute a class of actions effectively.

---

## 4) Relationship grammar (how entities relate)

The EBG relationship system should express causality, authority, accountability, and learning.

### 4.1 Intent relationships
- **Goal** is measured by **KPI**.
- **Goal** is limited by **Constraint**.
- **Trade-off** connects competing **Goals/KPIs**.

### 4.2 Human and power relationships
- **Employee** belongs to **Department**.
- **Manager** supervises **Employee/Manager**.
- **Role** is held by **Employee**.
- **Incentive** influences **Employee/Role/Department** behavior.

### 4.3 Decision relationships
- **Decision** advances or harms **Goal/KPI**.
- **Decision** depends on **Assumption**.
- **Decision** requires **Approval** from actors/roles.
- **Decision** creates **Action** commitments.
- **Decision** is constrained by **Policy/Constraint/Risk**.

### 4.4 Coordination relationships
- **Meeting** produces/modifies **Decision**, **Assumption**, **Conflict**, **Action**, **Approval**.
- **Conflict** blocks or delays **Decision/Action/Approval**.
- **Exception** temporarily suspends **Policy/Constraint** for a **Decision/Action**.

### 4.5 Execution and consequence relationships
- **Action** changes risk state and influences **Outcome**.
- **Outcome** validates or falsifies **Assumption**.
- **Outcome** updates **KPI** and progress toward **Goal**.
- **Dependency** orders **Action/Decision** execution sequence.

### 4.6 Learning relationships
- Repeated **Outcome** patterns become **Knowledge**.
- **Knowledge** updates **Policy**, **Decision heuristics**, and **Incentive design**.
- **Knowledge** changes future **confidence** in assumptions and actions.

---

## 5) Temporal evolution (how entities evolve)

Each entity has a lifecycle state and revision path.

### 5.1 Generic lifecycle template
$$
\text{Draft} \rightarrow \text{Proposed} \rightarrow \text{Committed} \rightarrow \text{Executed/Observed} \rightarrow \text{Reviewed} \rightarrow \text{Retired or Institutionalized}
$$

### 5.2 Key lifecycle examples
- **Assumption:** hypothesis → tested → supported/invalidated → archived or promoted to knowledge.
- **Decision:** proposed options → selected option → approved → enacted → reviewed for effectiveness.
- **Policy:** created → applied → exceptions accumulate → revision or replacement.
- **Incentive:** designed → behavior response observed → distortion detected → recalibrated.

### 5.3 Versioning concept
Every important entity should carry:
- **as-of time**,
- **supersedes link**,
- **reason-for-change**,
- **decision/approval provenance**.

This preserves institutional continuity and prevents historical amnesia.

---

## 6) Confidence dynamics (how confidence changes)

Confidence is not static belief; it is an enterprise-level belief function.

### 6.1 Confidence as a property
Attach confidence to:
- **Assumption confidence** (belief before outcomes mature),
- **Decision confidence** (expected efficacy),
- **Knowledge confidence** (strength of evidence and transferability),
- **Risk confidence** (reliability of probability/impact estimates).

### 6.2 Confidence update logic
Conceptually:
$$
C_{t+1} = f(C_t, E^+, E^-, Q, R, \Delta t)
$$
Where:
- $E^+$ = supporting evidence,
- $E^-$ = contradicting evidence,
- $Q$ = evidence quality,
- $R$ = relevance to current context,
- $\Delta t$ = time decay without fresh validation.

### 6.3 Confidence failure patterns
- Overconfidence from small sample wins.
- False certainty from politically filtered reporting.
- Stale confidence when context shifts but beliefs remain unchanged.

---

## 7) Memory architecture (how memory accumulates)

Institutional memory should be represented as four interacting memory types.

### 7.1 Episodic memory (what happened)
- Decisions, meetings, actions, outcomes, exceptions.
- Time-ordered and actor-attributed.

### 7.2 Semantic memory (what is generally true)
- Policies, validated knowledge, definitions, reusable patterns.

### 7.3 Procedural memory (how we do things)
- Playbooks, routines, escalation pathways, review rituals.

### 7.4 Causal memory (why things happen)
- Assumption → action → outcome chains,
- recurrent drivers of success/failure,
- known trade-off consequences.

### 7.5 Compounding mechanism
Memory compounds when:
1. outcomes are attributed to decisions/actions,
2. attribution is reviewed honestly,
3. insights are encoded into policy/incentives/routines,
4. future decisions consume that encoded learning.

Without this loop, the organization repeats mistakes with new vocabulary.

---

## 8) Long-horizon behavioural change (years, not quarters)

Organisational behavior changes through reinforcement loops.

### 8.1 Positive loop (intelligence compounding)
Better attribution → better decisions → better outcomes → higher trust in system → wider adoption → richer memory.

### 8.2 Negative loop (political regression)
Low accountability → narrative manipulation → weak learning → repeated failure → blame culture → reduced transparency.

### 8.3 Multi-year shifts to model explicitly
- Incentive redesign and second-order effects.
- Policy hardening vs adaptability.
- Leadership turnover and memory continuity breaks.
- Departmental cooperation drift (improves or fragments).
- Risk appetite cycles after major failures/successes.

### 8.4 Behavioural maturity stages
1. **Reactive:** fragmented decisions, weak attribution.  
2. **Structured:** explicit owners, standardized review.  
3. **Learning:** confidence-calibrated decisions and policy updates.  
4. **Adaptive:** rapid cross-functional trade-off optimization.  
5. **Institutional intelligence:** organization self-corrects faster than environment changes.

---

## 9) Minimal conceptual kernels of the “OS of organisational intelligence”

These are conceptual functions (not software modules):

1. **Sense** — capture events, outcomes, and context shifts.  
2. **Interpret** — link evidence to assumptions, risks, and goals.  
3. **Commit** — create accountable decisions with explicit trade-offs.  
4. **Coordinate** — align dependencies across departments and roles.  
5. **Execute** — drive actions and monitor consequence chains.  
6. **Learn** — promote validated patterns into knowledge/policy/incentives.  
7. **Adapt** — revise goals, constraints, and behavior under new conditions.

If any kernel is weak, intelligence quality degrades system-wide.

---

## 10) Canonical enterprise behaviour chain

A typical chain in the EBG:

**Risk signal** → **Meeting** → **Assumptions surfaced** → **Decision with trade-offs** → **Approvals** → **Actions** → **Outcomes** → **KPI movement** → **Confidence updates** → **Knowledge formation** → **Policy/Incentive adjustment** → **new baseline behavior**.

---

## 11) Anti-patterns the model must expose

- Decision without explicit assumption.
- Action without accountable owner.
- Outcome without attribution.
- Exception without expiry/review.
- KPI improvement with enterprise-value decline (local optimization trap).
- Policy proliferation without behavioral impact.
- Confidence that never decays despite old evidence.

These anti-patterns are early warnings of organizational intelligence failure.

---

## 12) Final definition

The Enterprise Behaviour Graph is the conceptual nervous system of the enterprise: a time-aware map of goals, incentives, decisions, actions, outcomes, and learning under real political and economic constraints.

Its strategic value is not data collection — it is **institutional self-correction**.

An enterprise becomes truly intelligent when it can:
1. remember accurately,  
2. reason with calibrated confidence,  
3. adapt incentives and policies based on causal evidence, and  
4. improve collective decision quality faster than external complexity grows.