# Phase 5 — Bounded Contexts & Interaction Contracts (DDD Business Architecture)

**Status:** Draft for approval  
**Scope:** Business architecture only (no API, no implementation, no data design)  
**Foundation:** Frozen strategy, PRD V1, domain map, and EBG ontology

---

## 1) Purpose

Define a complete bounded-context architecture for the Enterprise Intelligence Platform and formalize interaction contracts between contexts so semantic integrity, accountability, and long-term scalability are preserved.

This phase establishes:
1. bounded context boundaries,
2. context ownership,
3. published and consumed event contracts,
4. anti-corruption layers (ACLs),
5. translation contexts,
6. upstream/downstream responsibility model.

---

## 2) Business rationale

Without bounded contexts, enterprise models fail through semantic collisions:
- “decision” means different things in different functions,
- value attribution is disputed,
- policy/risk semantics drift,
- learning cannot compound reliably.

Bounded contexts prevent this by ensuring each domain owns one language and one responsibility center, while contracts define how meanings cross boundaries safely.

---

## 3) Alternatives considered

### Option A — Single unified context for all domains
- **Pros:** easy top-level story
- **Cons:** semantic overload, political ambiguity, weak ownership
- **Verdict:** rejected

### Option B — Fully isolated contexts with minimal interaction
- **Pros:** clean autonomy
- **Cons:** brittle enterprise coordination, broken attribution chain
- **Verdict:** rejected

### Option C — Federated bounded contexts with explicit contracts and translation (chosen)
- **Pros:** semantic rigor + cross-domain interoperability + scalable governance
- **Cons:** requires strong contract governance discipline
- **Verdict:** selected

---

## 4) Bounded context catalog and ownership

## Core Contexts

### BC-DA — Decision Accountability Context
- **Owns language of:** Decision, Assumption, Approval, TradeOff, Commitment state.
- **Primary ownership:** Chief Product Officer (product policy) + COO operating sponsor.
- **Mandate:** commitment integrity and accountable decision formation.

### BC-VR — Value Realization Context
- **Owns language of:** ValueAttributionCase, Economic Loss Avoided, realization variance.
- **Primary ownership:** CFO office.
- **Mandate:** accepted causal-attribution and economic impact proof.

### BC-CD — Coordination & Dependency Context
- **Owns language of:** Dependency, Escalation, coordination health, commitment reliability.
- **Primary ownership:** COO / Transformation office.
- **Mandate:** cross-functional dependency resolution and execution reliability.

### BC-LM — Learning & Memory Context
- **Owns language of:** EvidenceArtifact, CausalClaim, KnowledgePattern, Doctrine, MaturityState.
- **Primary ownership:** Chief AI Scientist + CPO governance council.
- **Mandate:** compounding institutional intelligence.

### BC-IB — Incentive & Behaviour Alignment Context
- **Owns language of:** Incentive map, behavior distortion, alignment intervention.
- **Primary ownership:** COO + CFO co-ownership.
- **Mandate:** align local behavior with enterprise-value outcomes.

## Supporting Contexts

### BC-GK — Goal & KPI Governance Context
- **Primary ownership:** Strategy office + Finance.
- **Mandate:** objective hierarchy and KPI semantic integrity.

### BC-RP — Risk & Policy Governance Context
- **Primary ownership:** Risk/Compliance leadership.
- **Mandate:** policy/risk boundary semantics and exception pressure governance.

### BC-CR — Coordination Rituals Context
- **Primary ownership:** COO operating cadence office.
- **Mandate:** recurring review rhythm and closure discipline.

### BC-CE — Conflict & Exception Resolution Context
- **Primary ownership:** cross-functional governance board.
- **Mandate:** structured arbitration and exception lifecycle governance.

### BC-ST — Stakeholder Trust & Adoption Economics Context
- **Primary ownership:** CEO/CPO/COO joint.
- **Mandate:** sponsor confidence and renewal/expansion trust conversion.

## Generic Contexts

### BC-IR — Identity/Role/Responsibility Context
- Ownership: enterprise governance office.

### BC-OR — Organizational Structure Context
- Ownership: operating model governance.

### BC-TC — Time & Operating Period Context
- Ownership: enterprise operating cadence governance.

### BC-TG — Taxonomy & Glossary Context
- Ownership: ontology stewardship council.

### BC-EP — Evidence Provenance & Audit Context
- Ownership: governance assurance office.

### BC-BM — External Benchmark Context
- Ownership: strategy intelligence office.

---

## 5) Interaction contract model (business-level)

Every context interaction contract has:
1. **Business purpose**  
2. **Upstream publisher context**  
3. **Downstream consumer context(s)**  
4. **Published event semantics**  
5. **Consumed event semantics**  
6. **Consumer obligations**  
7. **Semantic risks**  
8. **ACL requirement**  
9. **Translation context (if required)**

---

## 6) Primary interaction contracts

## IC-01: Goal intent into decision formation
- **Purpose:** ensure decisions are objectively anchored.
- **Publisher:** BC-GK
- **Consumers:** BC-DA, BC-VR, BC-IB
- **Published events:** GoalDefined, GoalAdjusted, KPIDefined, KPIReclassified
- **Consumer obligations:** map decisions/claims/interventions to current objective semantics.
- **ACL:** required for legacy/local KPI vocabularies.
- **Translation context:** **TCX-GoalSemanticBridge**

## IC-02: Policy/risk boundary into commitments
- **Purpose:** ensure commitments respect governance boundaries.
- **Publisher:** BC-RP
- **Consumers:** BC-DA, BC-CD, BC-CE
- **Published events:** PolicyActivated, PolicySuperseded, RiskEscalated, ControlDeemedIneffective
- **Consumer obligations:** challenge/hold decisions and actions when risk-policy guards fail.
- **ACL:** required when local risk ratings differ from canonical risk classes.
- **Translation context:** **TCX-RiskPolicyNormalization**

## IC-03: Decision commitments into coordination execution
- **Purpose:** convert committed decisions into dependency-aware execution commitments.
- **Publisher:** BC-DA
- **Consumers:** BC-CD, BC-CR, BC-CE
- **Published events:** DecisionCommitted, DecisionChallenged, DecisionReversed, ApprovalConditioned
- **Consumer obligations:** open dependencies, trigger escalations, synchronize cadence.
- **ACL:** required when local teams treat approvals as advisory rather than mandatory.
- **Translation context:** **TCX-CommitmentReliabilityBridge**

## IC-04: Coordination outcomes into value attribution
- **Purpose:** ensure attribution includes dependency/friction context.
- **Publisher:** BC-CD
- **Consumers:** BC-VR, BC-LM, BC-ST
- **Published events:** DependencyAtRisk, DependencyResolved, EscalationTriggered, CommitmentMissDiagnosed
- **Consumer obligations:** include coordination confounders in value and learning claims.
- **ACL:** required where delay semantics are inconsistent across units.
- **Translation context:** **TCX-ExecutionContextBridge**

## IC-05: Decision and execution outcomes into value realization
- **Purpose:** produce sponsor-accepted economic value claims.
- **Publishers:** BC-DA, BC-CD, BC-GK
- **Consumer:** BC-VR
- **Published events:** OutcomeObserved, KPIShiftObserved, DecisionReversalClassified, ActionReworked
- **Consumer obligations:** baseline comparison, confounder review, confidence scoring.
- **ACL:** required when business units use non-comparable baseline windows.
- **Translation context:** **TCX-ValueAttributionNormalization**

## IC-06: Attribution and evidence into learning promotion
- **Purpose:** transform accepted evidence into institutional knowledge.
- **Publisher:** BC-VR
- **Consumers:** BC-LM, BC-IB, BC-RP, BC-DA
- **Published events:** ValueCaseAccepted, ValueCaseContested, AttributionConfidenceChanged
- **Consumer obligations:** promote/retire patterns, update doctrine, trigger alignment reviews.
- **ACL:** required when evidence quality taxonomies differ.
- **Translation context:** **TCX-EvidenceQualityBridge**

## IC-07: Learning doctrine into policy and decision behavior
- **Purpose:** close the learning loop into future commitments.
- **Publisher:** BC-LM
- **Consumers:** BC-DA, BC-RP, BC-IB, BC-CR
- **Published events:** PatternPromoted, DoctrineUpdated, KnowledgeDecayed, MaturityRegressed
- **Consumer obligations:** adjust decision rules, policy pressure handling, ritual priorities.
- **ACL:** required where doctrine language conflicts with existing policy terms.
- **Translation context:** **TCX-DoctrineOperationalization**

## IC-08: Incentive misalignment into executive correction
- **Purpose:** convert behavioral distortion into governance action.
- **Publisher:** BC-IB
- **Consumers:** BC-DA, BC-VR, BC-ST, BC-CE
- **Published events:** MisalignmentDetected, AlignmentInterventionApproved, DistortionRecurrenceDetected
- **Consumer obligations:** adjust commitments, attribution assumptions, sponsor risk posture.
- **ACL:** required where incentive terminology is politically sanitized.
- **Translation context:** **TCX-IncentiveImpactBridge**

## IC-09: Conflict/exception pressure into decision and policy correction
- **Publisher:** BC-CE
- **Consumers:** BC-DA, BC-RP, BC-CD, BC-LM
- **Published events:** ConflictDeclared, ConflictResolved, ExceptionApproved, ExceptionExpired, ExceptionConvertedToPolicyInput
- **Consumer obligations:** re-evaluate commitments, update policy, record learning implications.
- **ACL:** required for unit-specific exception semantics.
- **Translation context:** **TCX-ExceptionPolicyBridge**

## IC-10: Value proof and maturity signals into trust & adoption
- **Publishers:** BC-VR, BC-LM, BC-CD
- **Consumer:** BC-ST
- **Published events:** ValueCaseAccepted, MaturityAdvanced, ReliabilityTrendImproved, AttributionChallenged
- **Consumer obligations:** renew/expand readiness updates and sponsor confidence governance.
- **ACL:** required where trust signals are anecdotal vs evidential.
- **Translation context:** **TCX-TrustEvidenceBridge**

---

## 7) Context-level event publication and consumption matrix

## 7.1 Core contexts

### BC-DA
- **Publishes:** DecisionProposed, DecisionApproved, DecisionCommitted, DecisionChallenged, DecisionReversed, ApprovalConditioned
- **Consumes:** GoalDefined, KPIDefined, PolicyActivated, RiskEscalated, ConflictDeclared, DoctrineUpdated, MisalignmentDetected

### BC-VR
- **Publishes:** ValueCaseOpened, ValueCaseAccepted, ValueCaseContested, AttributionConfidenceChanged
- **Consumes:** DecisionCommitted, OutcomeObserved, KPIShiftObserved, DependencyAtRisk/Resolved, EvidenceAdded

### BC-CD
- **Publishes:** DependencyDeclared, DependencyAtRisk, DependencyResolved, EscalationTriggered, CommitmentReliabilityChanged
- **Consumes:** DecisionCommitted, ApprovalConditioned, ConflictDeclared, PolicySuperseded

### BC-LM
- **Publishes:** CausalClaimValidated, PatternPromoted, DoctrineUpdated, KnowledgeDecayed, MaturityAdvanced/Regressed
- **Consumes:** ValueCaseAccepted/Contested, OutcomeObserved, ExceptionConvertedToPolicyInput, MisalignmentDetected

### BC-IB
- **Publishes:** MisalignmentDetected, AlignmentInterventionProposed, AlignmentInterventionApproved, DistortionRecurrenceDetected
- **Consumes:** KPIShiftObserved, ValueCaseAccepted, PatternPromoted, ConflictResolved

## 7.2 Supporting contexts

### BC-GK
- **Publishes:** GoalDefined, GoalAdjusted, KPIDefined, KPIReclassified
- **Consumes:** ValueCaseAccepted, MisalignmentDetected, MaturityRegressed

### BC-RP
- **Publishes:** PolicyActivated, PolicySuperseded, RiskEscalated, ControlDeemedIneffective
- **Consumes:** ExceptionConvertedToPolicyInput, DoctrineUpdated, ConflictDeclared

### BC-CR
- **Publishes:** ReviewCycleOpened, ReviewCycleClosed, ClosureMissDetected
- **Consumes:** DecisionCommitted, EscalationTriggered, DoctrineUpdated

### BC-CE
- **Publishes:** ConflictDeclared, ConflictResolved, ExceptionApproved, ExceptionExpired, ExceptionConvertedToPolicyInput
- **Consumes:** DependencyAtRisk, PolicyActivated, DecisionChallenged

### BC-ST
- **Publishes:** SponsorConfidenceChanged, RenewalReadinessUpdated, ExpansionReadinessUpdated
- **Consumes:** ValueCaseAccepted/Contested, MaturityAdvanced/Regressed, ReliabilityTrendChanged

## 7.3 Generic contexts

### BC-IR / BC-OR / BC-TC / BC-TG / BC-EP / BC-BM
- **Publish:** semantic/reference updates (RoleChanged, UnitReorganized, PeriodBoundaryAdjusted, TermSuperseded, EvidenceCredibilityReclassified, BenchmarkUpdated)
- **Consume:** dependent context change requests and governance correction triggers.

---

## 8) Anti-Corruption Layers (ACLs)

ACLs are mandatory wherever external/local meanings could contaminate canonical context language.

## ACL inventory

1. **ACL-A: Goal/KPI Semantic ACL**  
   Protects BC-DA/BC-VR/BC-IB from local metric distortions.

2. **ACL-B: Policy/Risk Semantic ACL**  
   Protects decision/coordination contexts from inconsistent risk-policy interpretation.

3. **ACL-C: Commitment Semantics ACL**  
   Protects BC-CD from informal/non-binding decision language.

4. **ACL-D: Attribution Evidence ACL**  
   Protects BC-VR/BC-LM from weak or non-comparable evidence claims.

5. **ACL-E: Incentive Semantics ACL**  
   Protects BC-IB from politically disguised incentive terminology.

6. **ACL-F: Trust Signal ACL**  
   Protects BC-ST from anecdotal optimism replacing accepted value evidence.

7. **ACL-G: Taxonomy Drift ACL**  
   Protects all contexts from local vocabulary forks (through BC-TG).

---

## 9) Translation contexts

Translation contexts are neutral semantic bridges for concept harmonization between contexts.

## TCX catalog

1. **TCX-GoalSemanticBridge** — maps local objective vocab to canonical objective/KPI semantics.  
2. **TCX-RiskPolicyNormalization** — harmonizes risk class and policy severity language.  
3. **TCX-CommitmentReliabilityBridge** — translates local commitment states into canonical commitment integrity terms.  
4. **TCX-ExecutionContextBridge** — normalizes dependency/escalation terminology for attribution use.  
5. **TCX-ValueAttributionNormalization** — standardizes value-proof vocabulary and confidence framing.  
6. **TCX-EvidenceQualityBridge** — harmonizes evidence quality scales across functions/units.  
7. **TCX-DoctrineOperationalization** — translates learning doctrine into operational policy/decision language.  
8. **TCX-IncentiveImpactBridge** — maps incentive mechanism language to behavior/outcome terms.  
9. **TCX-ExceptionPolicyBridge** — aligns exception rationale language with policy revision semantics.  
10. **TCX-TrustEvidenceBridge** — translates evidence maturity into sponsor trust signals.

---

## 10) Context relationship patterns (DDD)

### Customer–Supplier patterns
- BC-GK -> BC-DA
- BC-GK -> BC-VR
- BC-RP -> BC-DA
- BC-DA -> BC-CD
- BC-DA -> BC-VR
- BC-VR -> BC-LM
- BC-LM -> BC-DA
- BC-LM -> BC-RP

### Partnership patterns
- BC-DA <-> BC-CD
- BC-DA <-> BC-CE
- BC-CD <-> BC-CR
- BC-VR <-> BC-LM
- BC-IB <-> BC-VR

### Conformist patterns
- BC-ST conforms to accepted evidence semantics from BC-VR/BC-LM
- BC-CE conforms to canonical policy semantics from BC-RP

### Shared Kernel patterns
- BC-TG shared semantic kernel for all contexts
- BC-EP shared provenance kernel for all evidence-sensitive contexts
- BC-TC shared time semantics kernel for all cadence/attribution contexts

---

## 11) Ownership model and decision rights

## 11.1 Context owners are semantic sovereigns
The owning context has final authority over:
- term definitions within boundary,
- event meaning within boundary,
- acceptance rules for inbound translated concepts.

## 11.2 Cross-context contract stewards
Each interaction contract has:
- one **Upstream Semantic Steward** (publisher owner),
- one **Downstream Integrity Steward** (consumer owner),
- one **Translation Steward** (translation context owner),
- one **Governance Arbiter** (ontology council representative).

## 11.3 Escalation rights
Contract disputes escalate in order:
1. Upstream/downstream stewards  
2. Translation steward mediation  
3. Ontology council arbitration  
4. Executive governance board final ruling

---

## 12) Invariants for interaction contracts

ICV-1. No context consumes a foreign concept without explicit contract semantics.  
ICV-2. No downstream context may redefine upstream canonical terms unilaterally.  
ICV-3. ACL usage is mandatory for high-risk semantic boundaries.  
ICV-4. Translation contexts do not own source or target domain truth; they only harmonize mapping.  
ICV-5. Every published event must have accountable publisher context owner.  
ICV-6. Every consumed event must specify consumer obligation.  
ICV-7. Contract changes require impact review across dependent contexts.

---

## 13) Risks

1. Contract sprawl and governance overhead.  
2. Translation-context overproliferation causing complexity drag.  
3. Hidden semantic forks inside business units.  
4. Political pressure to bypass ACL discipline.  
5. Event signal dilution from excessive publishing.

---

## 14) Failure modes

1. **Semantic Drift Failure** — KPI, risk, or commitment language diverges silently.  
2. **Attribution Fracture Failure** — value context consumes non-normalized execution semantics.  
3. **Governance Bypass Failure** — exceptions and policy interactions occur outside contracts.  
4. **Trust Distortion Failure** — sponsor trust context accepts narrative over validated evidence.  
5. **Learning Loop Break Failure** — learning context outputs do not re-enter decision and policy contexts.

---

## 15) Validation criteria

Architecture is valid if it can:
1. trace any accepted value claim across contexts without semantic ambiguity,  
2. reconstruct decision reversal causes across DA/CD/CE/RP contexts,  
3. show where every major event is published and consumed with clear ownership,  
4. demonstrate mandatory ACL boundaries at all high-risk semantic crossings,  
5. maintain stable meaning across industries via translation contexts, not core-term redefinition.

---

## 16) Acceptance criteria (Phase 5 gate)

Approve when all are true:
1. Every domain has an explicit bounded context.  
2. Ownership is unambiguous for each context and contract.  
3. Publish/consume event matrix is complete for core business flows.  
4. ACLs are defined for all high-risk semantic crossings.  
5. Translation contexts are explicitly named and scoped.  
6. Context-map patterns (customer-supplier/partnership/conformist/shared-kernel) are coherent.  
7. No API/implementation assumptions are required.

---

## 17) Recommendation

Adopt this bounded-context and interaction-contract architecture as the canonical business semantic operating model.

It is the minimum structure required to scale the platform globally while preserving:
- accountability integrity,
- value attribution credibility,
- governance defensibility,
- and long-term learning compounding.