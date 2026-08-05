# INTEGRATION_ARCHITECTURE.md

**Status:** Draft for approval (Phase 19 architecture)  
**Scope:** Canonical ERP-agnostic integration architecture governance and implementation-enabling constraints  
**Authority hierarchy:** Subordinate to `ENGINEERING_CONSTITUTION.md`; recorded under `docs/MASTER_ARCHITECTURE.md` Phase 19; implementation-enabling constraints grounded in approved reference architecture, bounded-context model, and engineering constitution  
**Constraint profile:** Planning/governance artifact only; additive-only; non-duplicative; MVP-first; no implementation authorization; no new business scope

**Canonical references (not superseded or duplicated):**
- `../MASTER_ARCHITECTURE.md`
- `../../ENGINEERING_CONSTITUTION.md`
- `REFERENCE_ARCHITECTURE.md`
- `PLUGIN_ARCHITECTURE.md`
- `../../PHASE_3_EBG_COMPLETE_ONTOLOGY_SPECIFICATION.md`
- `../../PHASE_5_BOUNDED_CONTEXTS_AND_INTERACTION_CONTRACTS.md`
- `../ADR/ADR-0001-reference-architecture-prerequisite.md`

---

## Purpose

Define the canonical ERP-agnostic integration architecture governance and the minimum implementation-enabling constraints so that integration adapters can be introduced without corrupting canonical context semantics, violating approved invariants, or bypassing bounded-context ownership.

---

## Business rationale

The approved engineering constitution establishes that unbounded integrations are the primary source of fragility and drift, that integrations must pass semantic translation governance before broad rollout, and that external assumptions must be treated as volatile. The approved reference architecture defines Layer L6 (Integration & Extension Layer) and extension point E3 for new integration adapters through integration contracts.

Leaving integration governance only distributed across those prior artifacts creates interpretation drift and weakens auditability at implementation time. This document consolidates the approved integration governance constraints into one canonical Phase 19 artifact, scoped to the MVP-first, ERPNext-first context, without prescribing adapters that have not been authorized by approved governance.

---

## Scope boundaries

This document is limited to governance and implementation-enabling constraints already supported by the approved canonical architecture.

It covers only:
1. The ERP-agnostic integration contract model that all integration adapters must conform to.
2. Anti-corruption and semantic translation governance obligations.
3. Extension point E3 inheritance and ADR escalation rules.
4. Integration quality review requirements.
5. Applicable NFR obligations for integration adapters.
6. ERPNext/Frappe as the one named initial concrete integration adapter (validating the contract model is immediately usable).

It does **not** create or authorize:
- SAP, Oracle, Microsoft Dynamics, or Salesforce adapters,
- message bus or enterprise middleware contracts (Kafka, RabbitMQ, MQ, or equivalent),
- external workflow engine integration (Temporal, Camunda, or equivalent),
- AI service, local inference, or remote model-API adapters,
- document ingestion (RAG) or retrieval pipeline adapters,
- tool execution adapters,
- integration adapter registry or discovery infrastructure,
- multi-tenant integration isolation (reserved for Phase 20),
- new product scope,
- new implementation scope,
- new bounded contexts,
- new architecture phases or roadmap items,
- changes to approved Sprint 1 through Sprint 4 implementation history,
- ratification of any pending architecture phase.

---

## Preservation constraints

1. `ENGINEERING_CONSTITUTION.md` remains the highest engineering authority.
2. `docs/MASTER_ARCHITECTURE.md` remains the canonical governance ledger and phase register.
3. Approved bounded-context ownership and interaction-contract rules remain unchanged.
4. Approved ontology invariants and business rules remain authoritative and are not modified by this document.
5. Approved reference architecture Layer L6, extension point E3, and related ADR triggers remain in effect and are not superseded.
6. Frozen baseline and approved implementation contracts remain preserved; this document introduces no implementation authorization.
7. Any contradiction discovered between this document and an already-approved artifact must be handled through ADR review and canonical ledger update rather than implicit reinterpretation.

---

## Integration architecture constitution

### 1) Canonical integration governance principles

The following integration principles are mandatory for all integration-related architecture and implementation decisions.  
Authority: `ENGINEERING_CONSTITUTION.md` Section 6 — Integration Principles.

**Purpose:** Ensure integrations preserve core semantics and contractual integrity.

**Core principle rules:**
1. Integrations must pass semantic translation governance before broad rollout.
2. Canonical contracts must be established before broad integration rollout.
3. External assumptions must be treated as volatile.
4. Integration contracts must include ownership and failure semantics.
5. Anti-corruption mappings must be documented for every integration.
6. Integration quality is reviewed in architecture governance.

No integration adapter may enter broad rollout without satisfying all of the above.

### 2) ERP-agnostic integration contract model

The integration architecture is ERP-agnostic. This means:

- The canonical integration contract model is defined at the semantic and governance level, not at the technology or platform level.
- Any ERP, enterprise system, or external service may be connected by implementing a conforming integration adapter without modifying the canonical contract model.
- No canonical bounded context may take a direct dependency on the internal semantics of any external system.

**An integration adapter must include:**
1. The canonical context it connects to (publisher or consumer).
2. The semantic mapping: how external concepts translate to canonical context concepts.
3. Failure semantics: how the adapter behaves when the external system is unavailable or returns unexpected state.
4. Anti-corruption layer specification: identifying which canonical terms are at risk of contamination from external terminology.
5. Consumer obligations: what the downstream canonical context must do upon receiving translated events.
6. Ownership and stewardship: who is accountable for the adapter's correctness and maintenance.

Authority: `ENGINEERING_CONSTITUTION.md` §6; `docs/Architecture/REFERENCE_ARCHITECTURE.md` §4, §5.

### 3) Anti-corruption and semantic translation governance

Anti-corruption layers (ACLs) are mandatory at every integration boundary where external semantics could contaminate canonical context language.

**Mandatory ACL requirements for all integration adapters:**
1. An ACL is required when the external system uses terminology that overlaps with but differs from canonical bounded-context terms.
2. The ACL must document the translation mapping explicitly.
3. No canonical context may consume external events without a declared translation or confirmation that semantics are equivalent.
4. Translation stewardship belongs to the integration adapter owner, not the consuming context owner.

**Semantic translation governance obligations:**
1. Translation mappings must be reviewed and approved before any integration adapter enters production use.
2. Changes to an existing translation mapping are subject to ADR review if they affect upstream or downstream contract obligations.
3. External system vocabulary changes that invalidate a translation mapping must trigger adapter-level review, not canonical context modification.

Authority: `ENGINEERING_CONSTITUTION.md` §6; `PHASE_5_BOUNDED_CONTEXTS_AND_INTERACTION_CONTRACTS.md` §8 (ACL inventory) and §9 (Translation contexts).

### 4) Extension point E3 inheritance

The approved reference architecture defines the following extension point applicable to this phase:

> **E3.** New integration adapters through integration contracts.

Authority: `docs/Architecture/REFERENCE_ARCHITECTURE.md` §8 — Extension points.

Extension point E3 is the approved mechanism for all integration adapters. No integration adapter may bypass context ownership or ontology invariants. Extension points E1, E2, E4, and E5 are governed separately and are not expanded by this document.

### 5) ERPNext/Frappe integration adapter (initial concrete example)

ERPNext/Frappe is the initial deployment platform for the Enterprise Intelligence Platform. This section defines the minimum contract model obligations for the ERPNext/Frappe integration adapter to validate the ERP-agnostic contract model is immediately usable.

**ERPNext adapter contract obligations:**
1. **Connecting context:** BC-DA (Decision Accountability) and BC-GK (Goal/KPI Governance) are the primary canonical contexts this adapter bridges.
2. **Semantic mapping obligation:** ERPNext DocType concepts (e.g., Project, Task, KPI targets) must be translated to canonical ontology concepts (Decision, Assumption, KPI, ActionCommitment) without importing ERPNext-specific semantics into canonical contexts.
3. **ACL requirement:** An ACL is mandatory between ERPNext terminology and all canonical contexts this adapter feeds.
4. **Failure semantics:** The adapter must define behavior when ERPNext is unavailable (fail-closed by default for governance-relevant events; observable and alertable).
5. **Ownership:** The ERPNext adapter owner is accountable for translation-mapping accuracy and for triggering review when ERPNext model changes occur.
6. **Extensibility:** This adapter definition must not couple canonical contexts directly to ERPNext internals; future migration to a different ERP must not require canonical context changes.

This example is illustrative of the contract model requirements. It does not authorize implementation beyond the governance obligations above.

Authority: `ENGINEERING_CONSTITUTION.md` §6; `PHASE_5_BOUNDED_CONTEXTS_AND_INTERACTION_CONTRACTS.md` §4, §6; `docs/Architecture/REFERENCE_ARCHITECTURE.md` §2, §5.

### 6) ADR escalation rules for integration architecture

ADR approval is required before proceeding with:

1. Any change to the integration contract model that affects existing adapter obligations.
2. Introduction of a new integration adapter beyond ERPNext that involves a new semantic mapping domain.
3. A change to an existing ACL translation mapping that affects upstream or downstream contract obligations.
4. A contract semantic change affecting upstream or downstream bounded-context obligations.
5. An integration that requires an invariant modification or exception extension.
6. An integration that changes security or privacy control model behavior.
7. An integration that introduces a compatibility-breaking change to a published adapter contract.
8. Introduction of any currently deferred adapter category (AI service, RAG, tool execution, message bus, external workflow engine).

Authority: `docs/Architecture/REFERENCE_ARCHITECTURE.md` §9 — Architectural decisions requiring ADR approval.

### 7) Integration quality review rules

1. Integration adapters are review-first and must satisfy the contract model before broad rollout.
2. Integration quality must be reviewed in architecture governance before any adapter is promoted to production use.
3. Governance reviewers must be able to trace integration contract semantics, ACL mappings, failure semantics, and ownership.
4. Translation mapping reviews are mandatory when the external system changes its data model or terminology.
5. No interpretation of this document may weaken approved accountability, invariant, traceability, or contract-governance obligations.

Authority: `ENGINEERING_CONSTITUTION.md` §6 acceptance criteria.

### 8) NFR obligations for integration adapters

All integration adapters must satisfy the mandatory NFR categories from the approved reference architecture. Each adapter must declare its NFR impact tier before merge.

**Mandatory NFR categories:**
1. Security — integration boundaries must not introduce unauthorized access paths.
2. Privacy — data crossing integration boundaries must respect provenance and purpose constraints.
3. Reliability — adapter failure behavior must be defined and observable.
4. Performance — integration latency must be declared and tier-appropriate.
5. Scalability — adapter design must not introduce global coupling that blocks scaling.
6. Observability — integration events must be observable and traceable.
7. Auditability — semantic mapping decisions and translation changes must be auditable.
8. Explainability — the integration's role in a decision or attribution chain must be reconstructable.

Authority: `docs/Architecture/REFERENCE_ARCHITECTURE.md` §7.

---

## Alternatives considered

1. **Leave integration governance only in the engineering constitution and reference architecture**
   - Pro: no additional document
   - Con: weaker auditability, higher interpretation drift at adapter implementation time
   - Verdict: rejected

2. **Create a multi-system integration specification covering SAP, Oracle, Salesforce, and others now**
   - Pro: comprehensive long-term coverage
   - Con: exceeds MVP-authorized scope; no approved governance mandates these systems; introduces premature complexity
   - Verdict: rejected

3. **Create a canonical ERP-agnostic integration contract model with ERPNext as the sole initial concrete example**
   - Pro: MVP-first, governance-compliant, future-extensible without modifying the canonical model
   - Con: requires discipline to not leak ERPNext-specific assumptions into the contract model
   - Verdict: selected

---

## Trade-offs

1. ERP-agnostic model requires more upfront contract governance discipline but prevents future lock-in.
2. Limiting MVP to ERPNext reduces initial scope but requires the contract model to be genuinely abstract or future adapters will require canonical model changes.
3. Deferring AI service, RAG, and tool-execution adapters keeps Phase 19 lean but requires each to be introduced through ADR when authorized.

---

## Risks

1. ERPNext adapter implementation leaks platform-specific semantics into canonical contexts despite ACL requirements.
2. Deferred adapter categories are introduced informally without ADR discipline.
3. Anti-corruption layers are treated as optional overhead rather than mandatory governance controls.
4. Teams may incorrectly assume this document authorizes code, schema, or API work beyond the governance obligations stated here.

---

## Failure modes

1. **Semantic Contamination Failure:** canonical context consumes ERPNext or external semantics directly without ACL translation.
2. **Contract Bypass Failure:** integration adapter introduced without conforming to the contract model.
3. **Invisible Coupling Failure:** ERPNext-specific assumptions hidden in integration code make future ERP migration require canonical changes.
4. **ACL Abandonment Failure:** translation mappings documented at first delivery but not maintained when external system changes.
5. **Scope Creep Failure:** deferred adapters introduced incrementally without ADR authorization.

---

## Implementation exclusions

This Phase 19 artifact does not:
- approve implementation,
- authorize new implementation scope beyond the governance obligations in this document,
- define ERPNext adapter APIs, schemas, sync mechanisms, or runtime contracts,
- define AI service, RAG, tool execution, message bus, or middleware adapters,
- define integration adapter registries or discovery infrastructure,
- address multi-tenant integration isolation (reserved for Phase 20),
- modify approved bounded-context ownership,
- alter approved ontology invariants,
- ratify any pending architecture phase,
- create exceptions to `ADR-0001`.

Implementation remains governed by the existing authority chain and execution rules recorded in `docs/MASTER_ARCHITECTURE.md`.

---

## Validation criteria

This architecture is valid if it:
1. Defines an ERP-agnostic integration contract model that any future adapter can conform to without modifying the canonical model.
2. Preserves the authority hierarchy across `ENGINEERING_CONSTITUTION.md` and `docs/MASTER_ARCHITECTURE.md`.
3. Correctly inherits extension point E3 and applicable ADR triggers from the approved reference architecture.
4. Makes anti-corruption, semantic translation governance, and contract obligation requirements deterministic.
5. Preserves approved bounded-context ownership and invariant obligations across integration boundaries.
6. Provides a concrete ERPNext example that validates the model is immediately usable.
7. Introduces no implementation, schema, API, tooling, or runtime assumptions.

---

## Acceptance criteria (Phase 19 gate)

Approve when all are true:
1. The document defines only integration architecture governance consolidation already supported by approved artifacts.
2. Scope boundaries and implementation exclusions are explicit and unambiguous, including all deferred categories.
3. Integration governance principles are consistent with `ENGINEERING_CONSTITUTION.md` Section 6.
4. The integration contract model is genuinely ERP-agnostic: specifying a new adapter for a different ERP should not require modifying the canonical model.
5. Extension point E3 and ADR triggers are correctly inherited from the approved reference architecture.
6. Anti-corruption, semantic translation, and ownership requirements are deterministic.
7. The ERPNext example validates the contract model is usable without exposing ERPNext-specific assumptions in the canonical model.
8. ADR escalation rules are deterministic and complete for the approved change categories.
9. Authority hierarchy and canonical recording rules remain unchanged.
10. No new business scope, feature scope, architecture phase, or implementation path is introduced beyond what is explicitly authorized here.
11. The document is auditable as a planning/governance artifact without requiring code, schema, or runtime assumptions.

---

## Approval status

This document is a **Phase 19 planning/governance artifact only** and is **waiting for independent specification audit** before any approval decision.
