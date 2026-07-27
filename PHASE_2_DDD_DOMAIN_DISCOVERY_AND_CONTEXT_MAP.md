# Phase 2 — Domain-Driven Design: Domain Discovery & Context Map

**Status:** Draft for approval  
**Scope:** Business architecture only (no software, no data model, no API, no implementation)  
**Foundation:** Built strictly on frozen artifacts (vision, strategy, buying psychology, EBG, PRD V1, value thesis)

---

## 1) Purpose

Define the complete business domain architecture of the Enterprise Intelligence Platform so the company can scale as a coherent enterprise system over 15 years.

This phase establishes:
1. all business domains,
2. their boundaries and responsibilities,
3. domain classification (Core / Supporting / Generic),
4. the DDD context map for long-term strategic clarity and defensibility.

---

## 2) Business rationale

Without explicit domain boundaries, enterprise platforms fail through:
- scope entropy,
- accountability confusion,
- duplicated capabilities,
- weak value attribution,
- politicized ownership conflicts.

Domain architecture is the intellectual operating backbone that preserves strategic focus while enabling controlled expansion.

---

## 3) Alternatives considered

### Option A — Functional decomposition by departments
- **Description:** mirror enterprise org chart (finance, operations, HR, etc.)
- **Pros:** easy to explain initially
- **Cons:** locks product to customer org structures; weak portability across industries
- **Verdict:** rejected

### Option B — Workflow-first decomposition only
- **Description:** define domains around specific workflows
- **Pros:** close to V1 execution pain
- **Cons:** fragments long-term platform; weak cross-workflow learning moat
- **Verdict:** partially useful, insufficient alone

### Option C — Capability-centered, decision-accountability architecture (chosen)
- **Description:** organize around enduring capabilities required for decision quality, attribution, and institutional learning
- **Pros:** scalable, defensible, consistent with frozen strategy and EBG
- **Cons:** requires stronger governance discipline upfront
- **Verdict:** selected

---

## 4) Design principles for domain discovery

1. **One domain = one business responsibility center.**  
2. **No domain owns another domain’s decisions.**  
3. **Core domains must directly create strategic differentiation.**  
4. **Supporting domains accelerate core outcomes but do not define category leadership.**  
5. **Generic domains are necessary but not strategic moats.**  
6. **Every domain must have measurable economic contribution.**

---

## 5) Domain inventory (complete business-domain set)

## 5.1 Core Domains (strategic moat)

### CD1. Decision Accountability
- **Purpose:** ensure every consequential decision has explicit owner, assumptions, trade-offs, and approval trace.
- **Business capability:** convert implicit decision behavior into explicit accountable commitments.
- **Boundaries:** starts at decision proposal; ends at committed decision with ownership and approval clarity.
- **Inputs:** goals, constraints, assumptions, conflicts, approval requirements.
- **Outputs:** committed decisions with accountable owner, rationale, trade-off statement.
- **Actors:** decision owners, approvers, cross-functional leaders.
- **Responsibilities:** decision integrity, ownership integrity, commitment finalization discipline.
- **Ownership:** Chief Product Officer (product policy) + COO sponsor (customer value reality).
- **Dependencies:** Goal & Value Governance, Risk & Policy Governance, Coordination & Conflict Resolution.
- **Events:** DecisionProposed, DecisionChallenged, DecisionCommitted, DecisionReversed.
- **Success metrics:** reversal rate, ownership clarity rate, decision cycle reliability.
- **Expansion potential:** multi-workflow rollout, multi-entity governance.
- **Future AI opportunities:** assumption quality scoring, trade-off scenario stress testing, reversal likelihood forecasting.

### CD2. Outcome Attribution & Value Realization
- **Purpose:** prove which decisions/actions generated which business outcomes and economic value.
- **Business capability:** translate operational behavior into attributable economic impact.
- **Boundaries:** starts at committed decision/action chain; ends at sponsor-accepted value attribution.
- **Inputs:** decision history, action history, KPI movement, confounder context.
- **Outputs:** attributable value claims, confidence-scored outcome chains.
- **Actors:** CFO office, COO office, workflow owners.
- **Responsibilities:** causal discipline, evidence quality control, value proof governance.
- **Ownership:** CFO-aligned value owner.
- **Dependencies:** Decision Accountability, KPI & Goal Governance, Learning & Institutional Memory.
- **Events:** OutcomeObserved, ValueAttributionChallenged, ValueAttributionAccepted.
- **Success metrics:** attribution confidence score, economic loss avoided, accepted value claims.
- **Expansion potential:** board-level value operating cadence; portfolio optimization.
- **Future AI opportunities:** confounder-aware attribution analysis, uncertainty-calibrated economic projections.

### CD3. Cross-Functional Coordination & Dependency Control
- **Purpose:** manage inter-team dependencies so commitments execute without hidden blockage.
- **Business capability:** expose and control dependency risk before it becomes reversal/rework.
- **Boundaries:** starts at inter-team dependency declaration; ends when dependency is resolved/escalated.
- **Inputs:** dependency declarations, resource commitments, timeline constraints.
- **Outputs:** dependency health state, escalation outcomes, coordination commitments.
- **Actors:** cross-functional coordinators, functional managers, escalation sponsors.
- **Responsibilities:** dependency visibility, escalation discipline, resolution cadence.
- **Ownership:** COO/Transformation office.
- **Dependencies:** Decision Accountability, Coordination Rituals, Risk Governance.
- **Events:** DependencyDeclared, DependencyAtRisk, DependencyResolved, EscalationTriggered.
- **Success metrics:** dependency delay rate, escalation resolution time, commitment hit-rate.
- **Expansion potential:** enterprise operating rhythm standardization.
- **Future AI opportunities:** early dependency-failure prediction, escalation prioritization assistance.

### CD4. Organisational Learning & Decision Memory
- **Purpose:** institutionalize decision/outcome learning so failures are not repeated and wins become doctrine.
- **Business capability:** convert episodic execution into compounding institutional intelligence.
- **Boundaries:** starts when decision-outcome cycles close; ends when validated patterns are promoted to reusable guidance.
- **Inputs:** reviewed outcomes, validated causal patterns, exceptions, policy impacts.
- **Outputs:** institutional knowledge, reusable decision patterns, maturity progression signals.
- **Actors:** domain leaders, governance leaders, executive review forums.
- **Responsibilities:** memory integrity, learning promotion criteria, doctrine upkeep.
- **Ownership:** Chief AI Scientist + CPO governance council.
- **Dependencies:** Outcome Attribution, Policy & Risk Governance, Incentive Alignment.
- **Events:** PatternDetected, PatternValidated, KnowledgePromoted, DoctrineRevised.
- **Success metrics:** knowledge promotion rate, repeat failure reduction, maturity stage progression.
- **Expansion potential:** cross-customer benchmarks, strategic advisory layer.
- **Future AI opportunities:** pattern extraction, confidence decay alerts, institutional forgetting risk detection.

### CD5. Incentive & Behaviour Alignment
- **Purpose:** align local incentives with enterprise outcomes to reduce coordination tax.
- **Business capability:** detect and correct incentive structures that drive harmful local optimization.
- **Boundaries:** starts at observed behavior distortion; ends at agreed incentive/policy adjustment recommendation.
- **Inputs:** behavior patterns, KPI distortions, conflict patterns, exception frequency.
- **Outputs:** incentive-risk insights, alignment recommendations, accountability implications.
- **Actors:** CFO, CHRO-adjacent stakeholders, BU leaders, COO.
- **Responsibilities:** identify misalignment, quantify enterprise cost, recommend correction paths.
- **Ownership:** COO + CFO co-ownership.
- **Dependencies:** Outcome Attribution, Conflict Resolution, Policy Governance.
- **Events:** MisalignmentDetected, AlignmentReviewInitiated, AlignmentAdjustmentAdopted.
- **Success metrics:** local-vs-enterprise KPI divergence reduction, conflict recurrence reduction.
- **Expansion potential:** enterprise incentive architecture advisory.
- **Future AI opportunities:** incentive distortion detection, behavioral drift forecasting.

---

## 5.2 Supporting Domains (enable core performance)

### SD1. Goal & KPI Governance
- **Purpose:** maintain coherent goals/KPI definitions and hierarchy.
- **Capability:** ensure decision quality is measured against stable, explicit enterprise intent.
- **Boundaries:** metric/goal semantics and governance only.
- **Inputs:** strategic priorities, functional targets.
- **Outputs:** goal hierarchy, KPI dictionary, target windows.
- **Actors:** strategy office, finance, operations leaders.
- **Responsibilities:** objective coherence, metric integrity.
- **Ownership:** strategy + finance.
- **Dependencies:** none upstream to core intent.
- **Events:** GoalDefined, KPIDefined, TargetAdjusted.
- **Success metrics:** KPI ambiguity reduction, goal conflict resolution speed.
- **Expansion potential:** multi-entity strategic planning coherence.
- **Future AI opportunities:** target plausibility stress testing.

### SD2. Risk & Policy Governance
- **Purpose:** govern policy constraints and risk boundaries for decision quality.
- **Capability:** ensure commitments remain within acceptable governance risk.
- **Boundaries:** policy and risk interpretation, not execution ownership.
- **Inputs:** risk signals, policy requirements, exceptions.
- **Outputs:** risk posture updates, policy interpretations, exception decisions.
- **Actors:** risk, legal, compliance, business owners.
- **Responsibilities:** control envelope, exception discipline.
- **Ownership:** risk/compliance leadership.
- **Dependencies:** Goal Governance, Decision Accountability.
- **Events:** PolicyUpdated, RiskReclassified, ExceptionApproved/Denied.
- **Success metrics:** policy breach reduction, exception cycle quality.
- **Expansion potential:** regulated-industry deepening.
- **Future AI opportunities:** policy conflict detection, risk escalation prioritization.

### SD3. Coordination Rituals & Operating Cadence
- **Purpose:** enforce recurring weekly/monthly decision-review rhythms.
- **Capability:** maintain operating discipline needed for attribution and learning.
- **Boundaries:** cadence governance, ritual quality standards.
- **Inputs:** decision/outcome backlog, escalations, open dependencies.
- **Outputs:** review outcomes, escalations, closure commitments.
- **Actors:** managers, coordinators, executive offices.
- **Responsibilities:** meeting quality, closure discipline, review completion.
- **Ownership:** COO transformation office.
- **Dependencies:** Decision Accountability, Dependency Control.
- **Events:** ReviewCycleOpened, ReviewCycleClosed, EscalationAssigned.
- **Success metrics:** review completion rate, closure latency, unresolved carryover rate.
- **Expansion potential:** enterprise operating model standardization.
- **Future AI opportunities:** meeting signal quality scoring, closure-risk alerts.

### SD4. Conflict & Exception Resolution
- **Purpose:** structure conflict handling and exception governance to prevent hidden organizational deadlocks.
- **Capability:** resolve incompatible objectives before they trigger costly reversals.
- **Boundaries:** conflict triage and resolution pathways, exception lifecycle.
- **Inputs:** conflict declarations, exception requests, trade-off disputes.
- **Outputs:** resolution outcomes, exception decisions, unresolved risk escalations.
- **Actors:** domain leaders, approvers, risk stakeholders.
- **Responsibilities:** conflict clarity, timely arbitration, exception expiry control.
- **Ownership:** cross-functional governance board.
- **Dependencies:** Decision Accountability, Risk & Policy Governance.
- **Events:** ConflictDeclared, ConflictResolved, ExceptionExpired.
- **Success metrics:** conflict resolution time, repeat conflict rate, expired exception compliance.
- **Expansion potential:** multi-business-unit arbitration model.
- **Future AI opportunities:** conflict-type clustering, exception abuse risk detection.

### SD5. Stakeholder Trust & Adoption Economics
- **Purpose:** manage executive confidence, sponsor continuity, and economic proof credibility.
- **Capability:** convert operational proof into renewal and expansion trust.
- **Boundaries:** buyer confidence and internal adoption economics; not product marketing ideation.
- **Inputs:** value proof outcomes, sponsor sentiment, adoption friction indicators.
- **Outputs:** trust health assessments, renewal readiness, expansion readiness.
- **Actors:** executive sponsor coalition, value owner, operating owners.
- **Responsibilities:** confidence maintenance, survivable change pacing.
- **Ownership:** CEO/CPO/COO joint responsibility.
- **Dependencies:** Outcome Attribution, Learning, Coordination Cadence.
- **Events:** SponsorConfidenceChanged, RenewalReadinessUpdated.
- **Success metrics:** sponsor confidence trend, renewal conversion, expansion conversion.
- **Expansion potential:** referenceability engine for global growth.
- **Future AI opportunities:** sponsor-risk prediction, adoption-friction forecasting.

---

## 5.3 Generic Domains (necessary, non-differentiating)

### GD1. Identity, Role, and Responsibility Registry
- **Purpose:** maintain clarity of actors and accountable roles.
- **Capability:** authoritative role/ownership reference for all domains.

### GD2. Organization Structure Reference
- **Purpose:** maintain departments, reporting lines, operating units.
- **Capability:** structural context for decision accountability.

### GD3. Time, Calendar, and Operating Period Reference
- **Purpose:** standard time windows for cycle analysis and cadence governance.
- **Capability:** temporal consistency.

### GD4. Taxonomy & Glossary Governance
- **Purpose:** maintain shared definitions for goals, risks, exceptions, outcomes.
- **Capability:** semantic consistency across domains.

### GD5. Evidence Provenance & Audit Trace
- **Purpose:** preserve source and credibility metadata for claims.
- **Capability:** trust and defensibility.

### GD6. External Benchmark Reference
- **Purpose:** maintain peer/industry reference context for comparative interpretation.
- **Capability:** contextualized executive decision support.

---

## 6) Domain classification summary

### Core Domains
1. Decision Accountability  
2. Outcome Attribution & Value Realization  
3. Cross-Functional Coordination & Dependency Control  
4. Organisational Learning & Decision Memory  
5. Incentive & Behaviour Alignment

### Supporting Domains
1. Goal & KPI Governance  
2. Risk & Policy Governance  
3. Coordination Rituals & Operating Cadence  
4. Conflict & Exception Resolution  
5. Stakeholder Trust & Adoption Economics

### Generic Domains
1. Identity, Role, Responsibility Registry  
2. Organization Structure Reference  
3. Time & Operating Period Reference  
4. Taxonomy & Glossary Governance  
5. Evidence Provenance & Audit Trace  
6. External Benchmark Reference

---

## 7) Context Map (DDD business-context relationships)

## 7.1 Primary flow of strategic value
Goal & KPI Governance  
→ Decision Accountability  
→ Coordination & Dependency Control  
→ Outcome Attribution & Value Realization  
→ Organisational Learning & Decision Memory  
→ Incentive & Behaviour Alignment  
→ back to Goal & KPI Governance (closed learning loop)

## 7.2 Relationship patterns (business-level)

- **Goal & KPI Governance -> Decision Accountability**  
  Pattern: **Customer–Supplier** (Decision Accountability consumes goal clarity)

- **Decision Accountability <-> Coordination & Dependency Control**  
  Pattern: **Partnership** (mutual success required for commitment reliability)

- **Decision Accountability -> Outcome Attribution**  
  Pattern: **Customer–Supplier** (attribution quality depends on decision integrity)

- **Outcome Attribution -> Organisational Learning**  
  Pattern: **Upstream/Downstream Knowledge Feed** (validated evidence fuels memory)

- **Organisational Learning -> Incentive & Behaviour Alignment**  
  Pattern: **Customer–Supplier** (learning identifies misalignment corrections)

- **Incentive & Behaviour Alignment -> Decision Accountability**  
  Pattern: **Feedback Partnership** (incentive correction improves future decision behavior)

- **Risk & Policy Governance -> all Core Domains**  
  Pattern: **Shared Kernel (Governance Rules)** where policy/risk semantics must remain consistent.

- **Conflict & Exception Resolution <-> Decision Accountability, Coordination, Risk**  
  Pattern: **Partnership + Escalation Context** (shared responsibility for deadlock removal)

- **Stakeholder Trust & Adoption Economics <-> Outcome Attribution, Learning**  
  Pattern: **Conformist to Evidence** (trust domain conforms to proven value evidence).

- **Generic Domains -> all domains**  
  Pattern: **Open Host Service equivalent at business level** (shared references available to all domains without redefining semantics).

## 7.3 Upstream/Downstream context responsibilities
- Upstream intent: Goal & KPI Governance, Risk & Policy Governance.
- Midstream execution intelligence: Decision Accountability, Coordination, Conflict/Exception.
- Downstream proof and adaptation: Outcome Attribution, Learning, Incentive Alignment, Trust/Adoption.

## 7.4 Context-map simplification test
A domain is retained only if removing it creates one of:
- accountability ambiguity,
- attribution collapse,
- learning-loop break,
- governance incoherence,
- renewal-risk increase.

All listed domains pass this necessity test.

---

## 8) Trade-offs

1. **Precision vs speed**  
   Strong accountability improves value proof but increases early behavior friction.

2. **Central governance vs local autonomy**  
   Consistency strengthens scale; excessive centralization can slow adaptation.

3. **Narrow V1 focus vs broad platform ambition**  
   Narrow focus enables proof; broader coverage deferred intentionally.

4. **Explicit conflict visibility vs political comfort**  
   Visibility improves correction but can increase short-term leadership tension.

---

## 9) Risks

1. Domain overlap drift as new use-cases appear.  
2. Incentive domain underpowered, causing repeated local optimization failures.  
3. Attribution challenged by confounders, weakening trust domain outcomes.  
4. Governance heaviness slowing operating cadence discipline.  
5. Leadership turnover breaking ownership continuity.

---

## 10) Failure modes

1. **Accountability theater:** decisions appear documented but ownership is symbolic.  
2. **Attribution theater:** value claims accepted politically, not evidentially.  
3. **Learning stagnation:** memory accumulates records but not doctrine changes.  
4. **Exception sprawl:** temporary exceptions become permanent loopholes.  
5. **Context fragmentation:** teams create parallel semantics, breaking coherence.

---

## 11) Validation criteria

This domain architecture is valid if it can:
1. explain every V1 KPI with clear domain ownership,  
2. trace any major reversal to domain responsibility and failure point,  
3. show closed-loop learning from decision to incentive/policy adaptation,  
4. support expansion from one workflow to many without redefining core domains,  
5. remain stable across industries with only workflow-specific tailoring.

---

## 12) Acceptance criteria (Phase 2 gate)

Approve Phase 2 when all are true:
1. Core/Supporting/Generic split is unambiguous.  
2. Every domain has explicit purpose, boundaries, actors, responsibilities, metrics.  
3. Context map has clear upstream/downstream and relationship patterns.  
4. No unnecessary domain remains after simplification test.  
5. Domain architecture fully supports frozen V1 PRD and value thesis.  
6. No software or implementation dependency is required to understand the model.

---

## 13) Recommendation

Adopt this domain architecture as the canonical business-context blueprint.

It is the simplest architecture that preserves:
- long-term strategic defensibility,
- measurable value attribution,
- cross-functional accountability,
- and compounding organizational learning.

Upon approval, the next phase should define **Business Capability Maps and Domain Policies** per core domain (still pre-implementation).