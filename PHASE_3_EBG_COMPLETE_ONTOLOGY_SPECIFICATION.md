# Phase 3 — Enterprise Behaviour Graph (EBG) Complete Ontology Specification

**Status:** Draft for approval  
**Scope:** Enterprise knowledge model only (no database, no API, no implementation)  
**Foundation:** Strictly derived from frozen artifacts (vision, strategy, PRD V1, DDD context map, buying psychology, value thesis)

---

## 1) Purpose

Define the complete ontology of the Enterprise Behaviour Graph so that the enterprise has a canonical model of:
- what exists (entities),
- how meaning is connected (relationships),
- what must always hold true (invariants),
- what behavior is allowed/required (business rules),
- how things evolve through time (lifecycles and transitions),
- what changes matter (event model).

This is the semantic constitution of organizational intelligence.

---

## 2) Business rationale

A platform that claims decision accountability and value attribution fails without a precise ontology because:
- accountability dissolves into interpretation,
- value proofs become politically contestable,
- cross-functional semantics fragment,
- institutional memory cannot compound reliably.

The ontology is the non-negotiable language layer required for multi-year scalability and defensibility.

---

## 3) Alternatives considered

### Option A — Minimal ontology (few entities, flexible semantics)
- **Pros:** rapid early usage
- **Cons:** ambiguity, weak attribution, poor auditability
- **Verdict:** rejected

### Option B — Workflow-specific ontology per customer
- **Pros:** local fit
- **Cons:** no durable platform semantics, low transferability
- **Verdict:** rejected

### Option C — Canonical enterprise ontology with extension points (chosen)
- **Pros:** stable core, controlled extensibility, defensible enterprise model
- **Cons:** requires stronger governance and ontology discipline
- **Verdict:** selected

---

## 4) Modelling conventions

1. **Entity** = stable concept with identity over time.  
2. **Relationship** = directed semantic link with explicit meaning.  
3. **Invariant** = always true if model integrity is preserved.  
4. **Business rule** = conditional norm that governs allowable behavior.  
5. **Lifecycle** = finite state progression for an entity category.  
6. **Event** = immutable record of meaningful domain change.  
7. **Transition** = state change triggered by event under rule guard conditions.

---

## 5) Ontology: complete entity catalog

## 5.1 Intent & Value Entities

### E1. EnterpriseObjective
- **Definition:** desired enterprise outcome at strategic or operational horizon.
- **Semantic role:** anchors why decisions exist.
- **Core properties (conceptual):** objective type, horizon, priority, owner role, scope.

### E2. KPI
- **Definition:** measurable signal used to track objective movement.
- **Semantic role:** evidence proxy for value progress.
- **Core properties:** metric definition, baseline window, target window, measurement confidence.

### E3. Constraint
- **Definition:** hard boundary condition limiting feasible choices.
- **Core properties:** source (regulatory/financial/capacity/policy), strictness, expiry.

### E4. TradeOff
- **Definition:** explicit acknowledgment of competing objective/KPI outcomes.
- **Core properties:** competing dimensions, accepted sacrifice, justification.

### E5. ValueHypothesis
- **Definition:** expected economic effect from a decision or action set.
- **Core properties:** expected impact range, confidence, time-to-impact.

---

## 5.2 Actor & Structure Entities

### E6. Actor
- **Definition:** human participant in enterprise behavior.
- **Core properties:** role assignment, authority level, organizational location.

### E7. Role
- **Definition:** responsibility template independent of specific person.
- **Core properties:** decision rights, approval rights, accountability obligations.

### E8. OrganizationalUnit
- **Definition:** formal unit (department/function/business unit).
- **Core properties:** unit mandate, leader role, unit objectives.

### E9. Incentive
- **Definition:** reward/penalty mechanism shaping behavior.
- **Core properties:** target behavior, beneficiary, cadence, conflict-risk score.

### E10. StakeholderPosition
- **Definition:** actor stance toward a decision/program (support/neutral/resist/block).
- **Core properties:** position state, rationale, influence level.

---

## 5.3 Decision & Governance Entities

### E11. Decision
- **Definition:** committed choice among alternatives with accountable ownership.
- **Core properties:** decision type, owner role, urgency, reversibility class, confidence.

### E12. Assumption
- **Definition:** uncertain belief used as basis for decision.
- **Core properties:** assumption class, confidence, falsifiability, expiry condition.

### E13. Approval
- **Definition:** authorization judgment by authorized actor/role.
- **Core properties:** approval type (required/discretionary), decision outcome, conditions.

### E14. Policy
- **Definition:** durable normative rule for allowable enterprise behavior.
- **Core properties:** policy scope, severity class, override policy.

### E15. Exception
- **Definition:** explicit temporary deviation from policy/constraint.
- **Core properties:** reason, approver, expiry, compensating controls.

### E16. Risk
- **Definition:** uncertain event/condition with potential negative objective impact.
- **Core properties:** likelihood estimate, impact estimate, confidence, owner.

### E17. Control
- **Definition:** mitigating practice to reduce risk likelihood/impact.
- **Core properties:** control strength, coverage, evidence of effectiveness.

---

## 5.4 Coordination & Execution Entities

### E18. CoordinationEpisode
- **Definition:** formal coordination instance (meeting/review/escalation ritual).
- **Core properties:** episode type, cadence type, facilitator role, closure state.

### E19. Conflict
- **Definition:** incompatible claims/targets/interpretations between actors or units.
- **Core properties:** conflict type, severity, affected objectives, status.

### E20. Dependency
- **Definition:** prerequisite relation where one commitment relies on another.
- **Core properties:** dependency type, criticality, due condition, blocker risk.

### E21. ActionCommitment
- **Definition:** accountable intervention agreed as consequence of a decision.
- **Core properties:** owner, due condition, success condition, reversibility.

### E22. OutcomeObservation
- **Definition:** observed effect following actions/decisions.
- **Core properties:** observed delta, confidence, attribution status, confounders.

### E23. EventSignal
- **Definition:** meaningful environmental/internal signal that may trigger review.
- **Core properties:** signal class, severity, source confidence.

---

## 5.5 Learning & Intelligence Entities

### E24. EvidenceArtifact
- **Definition:** supporting/contradicting evidence used in evaluation.
- **Core properties:** source quality, relevance, timestamp, provenance integrity.

### E25. CausalClaim
- **Definition:** explicit proposition linking cause path to outcome.
- **Core properties:** claim pattern, confidence, transferability class.

### E26. KnowledgePattern
- **Definition:** validated reusable pattern promoted from repeated causal evidence.
- **Core properties:** applicability envelope, confidence, decay profile.

### E27. Doctrine
- **Definition:** institutionalized guidance/rule derived from validated learning.
- **Core properties:** authority level, applicability scope, review cadence.

### E28. ConfidenceState
- **Definition:** calibrated belief state attached to assumptions/claims/risks.
- **Core properties:** numeric/confidence band, update rationale, decay rate.

### E29. MaturityState
- **Definition:** stage of organizational behavioral intelligence.
- **Core properties:** stage, evidence basis, progression barriers.

### E30. ValueAttributionCase
- **Definition:** bounded claim of economic impact tied to specific decision-action chain.
- **Core properties:** claimed value range, accepted value, confidence, sponsor acceptance.

---

## 6) Complete relationship ontology

Notation: **A -[relation]-> B**

## 6.1 Intent relationships
1. EnterpriseObjective -[is_measured_by]-> KPI  
2. EnterpriseObjective -[is_limited_by]-> Constraint  
3. TradeOff -[balances]-> EnterpriseObjective  
4. TradeOff -[balances]-> KPI  
5. ValueHypothesis -[predicts_movement_in]-> KPI

## 6.2 Actor and power relationships
6. Actor -[holds]-> Role  
7. Actor -[belongs_to]-> OrganizationalUnit  
8. Role -[governs_rights_over]-> Decision  
9. Incentive -[influences]-> Actor  
10. Incentive -[influences]-> OrganizationalUnit  
11. StakeholderPosition -[is_position_of]-> Actor  
12. StakeholderPosition -[targets]-> Decision

## 6.3 Decision and governance relationships
13. Decision -[advances_or_harms]-> EnterpriseObjective  
14. Decision -[is_justified_by]-> Assumption  
15. Decision -[requires]-> Approval  
16. Decision -[is_constrained_by]-> Constraint  
17. Decision -[is_governed_by]-> Policy  
18. Decision -[accepts]-> TradeOff  
19. Decision -[creates]-> ActionCommitment  
20. Decision -[is_exposed_to]-> Risk  
21. Exception -[overrides_temporarily]-> Policy  
22. Exception -[overrides_temporarily]-> Constraint  
23. Control -[mitigates]-> Risk

## 6.4 Coordination relationships
24. CoordinationEpisode -[produces_or_updates]-> Decision  
25. CoordinationEpisode -[produces_or_updates]-> Assumption  
26. CoordinationEpisode -[produces_or_updates]-> Conflict  
27. CoordinationEpisode -[produces_or_updates]-> ActionCommitment  
28. CoordinationEpisode -[produces_or_updates]-> Approval  
29. Conflict -[blocks_or_delays]-> Decision  
30. Conflict -[blocks_or_delays]-> ActionCommitment  
31. Dependency -[blocks_if_unmet]-> ActionCommitment  
32. Dependency -[blocks_if_unmet]-> Decision

## 6.5 Execution and outcome relationships
33. ActionCommitment -[implements]-> Decision  
34. ActionCommitment -[depends_on]-> Dependency  
35. ActionCommitment -[changes]-> Risk  
36. OutcomeObservation -[results_from]-> ActionCommitment  
37. OutcomeObservation -[validates_or_falsifies]-> Assumption  
38. OutcomeObservation -[moves]-> KPI  
39. EventSignal -[triggers_review_of]-> Decision

## 6.6 Learning relationships
40. EvidenceArtifact -[supports_or_contradicts]-> CausalClaim  
41. CausalClaim -[links]-> Decision  
42. CausalClaim -[links]-> ActionCommitment  
43. CausalClaim -[links]-> OutcomeObservation  
44. CausalClaim -[is_promoted_to]-> KnowledgePattern  
45. KnowledgePattern -[informs]-> Doctrine  
46. Doctrine -[updates]-> Policy  
47. Doctrine -[updates]-> Decision  
48. ConfidenceState -[qualifies]-> Assumption  
49. ConfidenceState -[qualifies]-> CausalClaim  
50. ConfidenceState -[qualifies]-> Risk  
51. ValueAttributionCase -[is_based_on]-> CausalClaim  
52. ValueAttributionCase -[quantifies]-> ValueHypothesis  
53. MaturityState -[characterizes]-> OrganizationalUnit

---

## 7) Global invariants (must always hold)

## 7.1 Identity invariants
I1. Every Decision has exactly one accountable owner Role at commitment time.  
I2. Every Approval references one Decision and one approving Actor/Role.  
I3. Every ActionCommitment references one originating Decision.  
I4. Every Exception has an expiry condition.

## 7.2 Accountability invariants
I5. No committed Decision exists without at least one explicit Assumption.  
I6. No Decision may be marked committed unless required Approvals are satisfied.  
I7. No OutcomeObservation can be marked attributable without at least one explicit CausalClaim.

## 7.3 Governance invariants
I8. If a Policy is overridden, an Exception must exist and be approved.  
I9. Every high-severity Risk must have an owner Role.  
I10. Every active Exception must specify compensating control intent.

## 7.4 Learning invariants
I11. KnowledgePattern cannot be promoted without repeated supporting evidence across more than one cycle context.  
I12. Doctrine cannot be updated without a documented causal rationale.  
I13. ConfidenceState must include update rationale whenever it changes.

## 7.5 Time invariants
I14. State transitions must be event-triggered and time-ordered (no temporal inversion).  
I15. Superseded entities remain part of institutional memory; they are not semantically erased.

---

## 8) Business rules (complete normative rule set)

## 8.1 Decision quality rules
R1. A Decision proposal must declare objective impact, assumptions, and trade-offs before approval routing.  
R2. Reversible and irreversible decisions must be explicitly classified before commitment.  
R3. Any Decision reversal requires reversal reason classification and review trigger.

## 8.2 Approval rules
R4. Approval rights are role-bound, not person-bound.  
R5. Conditional approvals must encode conditions that are observable and reviewable.  
R6. If approval conditions fail post-commitment, Decision enters challenged state.

## 8.3 Exception rules
R7. Exception must include expiry, owner, and remediation intent.  
R8. Exception cannot be renewed without explicit review of prior outcome effects.  
R9. Repeated exception pattern triggers policy-review obligation.

## 8.4 Dependency and coordination rules
R10. Critical dependencies must be declared before commitment finalization.  
R11. Unresolved critical dependency blocks ActionCommitment start.  
R12. Dependency risk escalation is mandatory when due condition breach risk exceeds threshold.

## 8.5 Attribution and evidence rules
R13. Value claims must reference baseline definition and confounder assessment.  
R14. Attribution confidence must decrease when evidence freshness decays beyond defined window.  
R15. Sponsor acceptance is required for case closure as accepted value.

## 8.6 Learning rules
R16. Unsupported or contradicted assumptions must be revised, retired, or explicitly risk-accepted.  
R17. Knowledge promotion requires evidence diversity (time, context, actor participation).  
R18. Doctrine updates must propagate to affected decision and policy contexts.

## 8.7 Incentive alignment rules
R19. If KPI improvement coexists with enterprise objective deterioration, misalignment review is mandatory.  
R20. Incentive changes require expected behavioral effect hypothesis and post-change review.

## 8.8 Integrity and transparency rules
R21. Critical decisions cannot be closed with unknown owner, unknown assumptions, or unknown review date.  
R22. Any high-value Decision must have scheduled outcome review obligation.  
R23. Confidence changes must be explainable to governance reviewers.

---

## 9) Lifecycles and state models

## 9.1 Decision lifecycle
States:
1. Draft  
2. Proposed  
3. UnderReview  
4. Approved  
5. Committed  
6. Challenged  
7. Reversed  
8. Closed

Transition highlights:
- Draft -> Proposed (on DecisionProposed)
- Proposed -> UnderReview (on ReviewInitiated)
- UnderReview -> Approved (on RequiredApprovalsSatisfied)
- Approved -> Committed (on CommitmentDeclared)
- Committed -> Challenged (on ContradictorySignalRaised)
- Challenged -> Reversed (on ReversalAuthorized)
- Committed -> Closed (on OutcomeReviewCompleted)

## 9.2 Assumption lifecycle
States:
1. Stated  
2. Active  
3. Tested  
4. Supported  
5. Contradicted  
6. Retired  
7. PromotedToKnowledge

## 9.3 Approval lifecycle
States:
1. Requested  
2. InEvaluation  
3. Approved  
4. ConditionallyApproved  
5. Rejected  
6. Withdrawn

## 9.4 Policy lifecycle
States:
1. Drafted  
2. Active  
3. UnderExceptionPressure  
4. UnderRevision  
5. Superseded  
6. Retired

## 9.5 Exception lifecycle
States:
1. Requested  
2. ApprovedActive  
3. Monitored  
4. Expired  
5. Revoked  
6. ConvertedToPolicyRevisionInput

## 9.6 Risk lifecycle
States:
1. Identified  
2. Assessed  
3. Accepted  
4. Mitigated  
5. Escalated  
6. Closed

## 9.7 ActionCommitment lifecycle
States:
1. Planned  
2. Authorized  
3. InProgress  
4. Completed  
5. Reworked  
6. Abandoned

## 9.8 OutcomeObservation lifecycle
States:
1. Observed  
2. PreliminaryAttributed  
3. Challenged  
4. AcceptedAttributed  
5. Archived

## 9.9 CausalClaim lifecycle
States:
1. Proposed  
2. UnderEvidenceReview  
3. ProvisionallyAccepted  
4. Validated  
5. Rejected  
6. PromotedToPattern

## 9.10 KnowledgePattern lifecycle
States:
1. Candidate  
2. Validated  
3. ActiveGuidance  
4. Revalidated  
5. Decayed  
6. Retired

## 9.11 ValueAttributionCase lifecycle
States:
1. Open  
2. QuantifiedDraft  
3. SponsorReview  
4. Accepted  
5. Contested  
6. Closed

---

## 10) Event taxonomy (complete event catalog)

## 10.1 Decision events
- DecisionDrafted
- DecisionProposed
- DecisionReviewInitiated
- DecisionApproved
- DecisionConditionallyApproved
- DecisionRejected
- DecisionCommitted
- DecisionChallenged
- DecisionReversed
- DecisionClosed

## 10.2 Assumption events
- AssumptionStated
- AssumptionActivated
- AssumptionTested
- AssumptionSupported
- AssumptionContradicted
- AssumptionRetired
- AssumptionPromoted

## 10.3 Approval events
- ApprovalRequested
- ApprovalGranted
- ApprovalConditioned
- ApprovalRejected
- ApprovalWithdrawn

## 10.4 Policy and exception events
- PolicyActivated
- PolicySuperseded
- ExceptionRequested
- ExceptionApproved
- ExceptionExpired
- ExceptionRevoked
- ExceptionConvertedToPolicyInput

## 10.5 Risk and control events
- RiskIdentified
- RiskAssessed
- RiskEscalated
- RiskMitigationActivated
- RiskClosed
- ControlDeemedIneffective

## 10.6 Coordination and dependency events
- CoordinationEpisodeOpened
- CoordinationEpisodeClosed
- ConflictDeclared
- ConflictResolved
- DependencyDeclared
- DependencyAtRisk
- DependencyResolved
- EscalationTriggered

## 10.7 Action and outcome events
- ActionPlanned
- ActionAuthorized
- ActionStarted
- ActionCompleted
- ActionReworked
- OutcomeObserved
- OutcomeAttributionChallenged
- OutcomeAttributionAccepted

## 10.8 Learning and value events
- EvidenceAdded
- CausalClaimProposed
- CausalClaimValidated
- CausalClaimRejected
- PatternDetected
- PatternPromoted
- DoctrineUpdated
- ConfidenceUpdated
- ValueCaseOpened
- ValueCaseAccepted
- ValueCaseContested
- ValueCaseClosed

---

## 11) State transition rules (guard conditions)

## 11.1 Decision transition guards
G1. Proposed -> UnderReview requires at least one explicit Assumption and one objective link.  
G2. UnderReview -> Approved requires mandatory approval set satisfied.  
G3. Approved -> Committed requires owner confirmation and dependency criticality declared.  
G4. Committed -> Closed requires at least one outcome review event.

## 11.2 Assumption transition guards
G5. Active -> Tested requires evidence plan declared.  
G6. Tested -> Supported/Contradicted requires evidence quality threshold met.  
G7. Supported -> PromotedToKnowledge requires repeated support in multiple cycles.

## 11.3 Exception transition guards
G8. Requested -> ApprovedActive requires policy owner approval + expiry condition.  
G9. ApprovedActive -> Expired occurs on expiry condition unless renewed under R8.  
G10. Repeated expiration with same pattern triggers ConvertedToPolicyRevisionInput.

## 11.4 Outcome attribution guards
G11. Observed -> PreliminaryAttributed requires proposed causal chain.  
G12. PreliminaryAttributed -> AcceptedAttributed requires confounder review and sponsor acceptance.  
G13. PreliminaryAttributed -> Challenged if contradictory evidence emerges.

## 11.5 Pattern promotion guards
G14. CausalClaim Validated -> PromotedToPattern requires evidence diversity and contradiction review closure.  
G15. KnowledgePattern ActiveGuidance -> Decayed if evidence freshness window breached.

---

## 12) Confidence ontology and update rules

## 12.1 Confidence object semantics
ConfidenceState applies to Assumption, Risk, CausalClaim, ValueAttributionCase.

Confidence dimensions:
1. Evidence strength
2. Evidence relevance
3. Evidence freshness
4. Context transferability
5. Contradiction pressure

## 12.2 Confidence update rule archetype
$C_{t+1} = f(C_t, E^+, E^-, Q, R, F, T, X)$
Where:
- $Q$ quality, $R$ relevance, $F$ freshness,
- $T$ transferability, $X$ contradiction intensity.

## 12.3 Confidence invariants
- Confidence cannot increase without new supporting evidence or improved evidence quality justification.  
- Confidence must decay when no revalidation occurs in defined windows.  
- High contradiction intensity must force review transition.

---

## 13) Cross-domain business rule matrix (condensed)

1. **Decision Accountability x Outcome Attribution**  
   No value claim without attributable decision-action chain.

2. **Decision Accountability x Conflict/Exception**  
   Conflicts and exceptions cannot remain unresolved beyond declared review windows.

3. **Policy/Risk x Action**  
   High-risk actions require explicit mitigation or risk acceptance.

4. **Learning x Incentive Alignment**  
   Repeated anti-patterns must trigger incentive review obligation.

5. **Goal/KPI x TradeOff**  
   Any significant KPI deterioration accepted for objective gain must be documented as explicit trade-off.

---

## 14) Trade-offs

1. **Semantic rigor vs adoption friction**  
   Rich ontology improves defensibility but increases discipline burden.

2. **Global consistency vs local flexibility**  
   Canonical language scales better but must allow bounded extensions.

3. **Attribution strictness vs speed**  
   Tight attribution improves credibility but can slow decision closure.

---

## 15) Risks

1. Over-complex ontology adoption failure.  
2. Political resistance to explicit ownership semantics.  
3. Confidence misuse (false precision).  
4. Event under-capture leading to memory holes.  
5. Governance fatigue causing rule bypass.

---

## 16) Failure modes

1. **Ontology Drift:** teams invent parallel semantics.  
2. **Accountability Theater:** formal owner exists but authority is not real.  
3. **Attribution Theater:** accepted value claims without causal quality.  
4. **Exception Laundering:** recurring exceptions become normalized bypass.  
5. **Learning Illusion:** records accumulate but doctrine never changes.

---

## 17) Validation criteria

The ontology is valid if it can:
1. represent every V1 KPI and explain ownership of KPI movement,  
2. reconstruct any major reversal from assumption to outcome,  
3. explain why confidence changed for any accepted value claim,  
4. support multi-year memory compounding without semantic resets,  
5. remain stable across customer industries with controlled extensions only.

---

## 18) Acceptance criteria (Phase 3 gate)

Approve when all are true:
1. Entity set is complete for V1 and near-term platform expansion.  
2. Relationship set is semantically unambiguous.  
3. Invariants and business rules are enforceable at governance level.  
4. Lifecycles and transitions cover operational and learning realities.  
5. Event taxonomy supports full accountability and attribution traceability.  
6. No database/API/implementation assumptions are required to use this model.

---

## 19) Recommendation

Adopt this ontology as the canonical enterprise knowledge model.

It is sufficiently rigorous to support:
- board-defensible value attribution,
- cross-functional decision accountability,
- multi-year organizational learning,
- and long-term platform defensibility as a global enterprise category leader.