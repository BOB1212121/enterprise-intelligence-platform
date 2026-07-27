# REFERENCE_ARCHITECTURE.md

**Status:** Draft for approval (Sprint 0 / S0-F1)  
**Constraint Profile:** Implementation-enabling, max-20-page equivalent, non-duplicative, model/language/framework agnostic  
**Canonical References (not duplicated):**
- `../MASTER_ARCHITECTURE.md`
- `../../PHASE_2_DDD_DOMAIN_DISCOVERY_AND_CONTEXT_MAP.md`
- `../../PHASE_3_EBG_COMPLETE_ONTOLOGY_SPECIFICATION.md`
- `../../PHASE_4_BUSINESS_CAPABILITY_MAP_BY_DOMAIN.md`
- `../../PHASE_5_BOUNDED_CONTEXTS_AND_INTERACTION_CONTRACTS.md`
- `../../PHASE_6_AI_REASONING_ARCHITECTURE_MODEL_AGNOSTIC.md`
- `../../ENGINEERING_CONSTITUTION.md`

---

## Purpose

Define the **minimum engineering decisions required before coding** so implementation can start immediately without violating approved business architecture.

---

## Business rationale

Coding without a reference architecture creates hidden coupling, semantic drift, and expensive rework.  
This document establishes only the engineering guardrails required for Sprint 0 execution.

---

## Alternative designs considered

1. **Full architecture compendium** before code
   - Pro: exhaustive
   - Con: blocks delivery, duplicates prior docs
   - Verdict: rejected

2. **Code-first with architecture inferred later**
   - Pro: speed illusion
   - Con: high rework/contradiction risk
   - Verdict: rejected

3. **Lean reference architecture baseline (chosen)**
   - Pro: enough structure to implement safely, no duplication
   - Con: requires disciplined ADR updates as implementation discovers edge cases
   - Verdict: selected

---

## Trade-offs

- Less up-front detail, more ADR discipline during execution.
- Strong boundary control may slow early shortcuts but prevents long-term entropy.
- Non-blocking stance for future architecture phases increases delivery speed but raises escalation responsibility.

---

## Risks

1. Teams treat references as optional and bypass boundaries.
2. PR velocity pressure erodes invariant enforcement.
3. “Temporary” coupling becomes permanent.
4. Missing ADRs make future reasoning opaque.

---

## Failure modes

1. **Semantic Coupling Failure** — one context reads another’s internals.
2. **Ownership Drift Failure** — KPI/decision/value ownership becomes ambiguous.
3. **Invariant Breach Failure** — implementations violate core decision/attribution rules.
4. **NFR Regression Failure** — scale/reliability/security ignored in early increments.

---

## The 10 required engineering answers

## 1) What are the platform layers?

L1. **Experience & Workflow Layer**  
Human-facing decision workflows and operational rituals.

L2. **Application Orchestration Layer**  
Use-case orchestration across bounded contexts.

L3. **Domain Services Layer**  
Business behavior owned by bounded contexts.

L4. **Reasoning & Learning Layer**  
Causal reasoning, confidence calibration, knowledge promotion.

L5. **Governance & Policy Layer**  
Rules, approvals, exception handling, trust controls.

L6. **Integration & Extension Layer**  
ERP/enterprise integration contracts + plugin extension boundaries.

L7. **Foundational Platform Layer**  
Cross-cutting concerns (security, observability, tenancy, reliability primitives).

> Layer definitions are conceptual constraints, not technology selections.

## 2) What are the engineering boundaries?

- Each bounded context is a semantic and ownership boundary.
- Cross-context interaction is allowed only via explicit published contracts.
- No context may directly depend on another context’s private semantics.
- Anti-corruption translation is mandatory on semantic mismatches.

## 3) Who owns each bounded context?

Canonical ownership is inherited from approved Phase 5 context map:
- **BC-DA** Decision Accountability — CPO + COO sponsor
- **BC-VR** Value Realization — CFO office
- **BC-CD** Coordination/Dependency — COO/Transformation
- **BC-LM** Learning/Memory — Chief AI Scientist + CPO council
- **BC-IB** Incentive Alignment — COO + CFO
- **BC-GK** Goal/KPI — Strategy + Finance
- **BC-RP** Risk/Policy — Risk/Compliance
- **BC-CR** Cadence/Rituals — COO cadence office
- **BC-CE** Conflict/Exception — Governance board
- **BC-ST** Trust/Adoption — CEO/CPO/COO
- Generic contexts per governance stewards in approved docs.

## 4) How do contexts communicate?

- Through **business event contracts** and **interaction contracts** only.
- Publisher defines event semantics; consumer defines obligation.
- Translation context mediates semantic mismatch.
- Contract evolution requires ADR when impact is material.

## 5) What data ownership rules are mandatory?

DOR-1. Data meaning is owned by the bounded context that owns the concept.  
DOR-2. No downstream context may redefine upstream canonical semantics.  
DOR-3. Shared references (identity/time/taxonomy/provenance) are consumed, not forked.  
DOR-4. Cross-context reuse requires contract + provenance + confidence metadata.  
DOR-5. Value attribution evidence must preserve baseline and confounder traceability.

## 6) What invariants must no implementation violate?

(From approved ontology; implementation must enforce)
- No committed decision without explicit assumption.
- No commitment without required approvals.
- No attributable outcome without explicit causal claim.
- No policy override without approved, expiring exception.
- No high-severity risk without owner.
- No confidence increase without evidence-quality rationale.

## 7) What non-functional requirements are mandatory?

Mandatory NFR categories for all production-bound capabilities:
1. Security
2. Privacy
3. Reliability
4. Performance
5. Scalability
6. Observability
7. Auditability
8. Explainability

Each feature must declare NFR impact tier and pass tier-appropriate checks before merge.

## 8) What extension points exist?

E1. New workflow templates within existing core domains  
E2. New context-level policy packs (without violating invariants)  
E3. New integration adapters through integration contracts  
E4. New plugin capabilities via extension contracts  
E5. New reasoning strategies that preserve confidence/causal governance

No extension may bypass context ownership or invariants.

## 9) What architectural decisions require ADR approval?

ADR is mandatory for:
- New bounded context creation or boundary change
- Contract semantic change affecting upstream/downstream obligations
- Invariant/rule modification or exception extension
- NFR target change for critical capability tiers
- Build-vs-buy decision in strategic/core capability paths
- Compatibility-breaking change
- Security/privacy control model change
- Plugin extension contract model change

## 10) What conditions must every pull request satisfy?

PR-C1. Linked requirement/user story with scope boundary.  
PR-C2. Context ownership identified.  
PR-C3. Contract impact identified (none / changed / new).  
PR-C4. Invariant impact declared and checked.  
PR-C5. Tests added/updated by risk tier.  
PR-C6. NFR impact declaration included.  
PR-C7. Documentation/ADR update included when architecture semantics change.  
PR-C8. No forbidden cross-context dependency introduced.

---

## Acceptance criteria

This reference architecture is approved when:
1. It answers all 10 required questions unambiguously.
2. It references prior approved architecture without duplicating it.
3. It defines only implementation-enabling decisions.
4. It remains concise (<=20-page equivalent).
5. It can be used immediately to initialize repository, CI/CD, testing, skeletons, and local runtime work.

---

## Post-approval execution policy

After approval of this document, Sprint 0 implementation proceeds immediately.  
No additional architecture document may block execution unless a **critical contradiction** is discovered and logged via ADR + master architecture update.