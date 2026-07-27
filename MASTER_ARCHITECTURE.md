# MASTER_ARCHITECTURE.md

**Status:** Living document (single source of architectural truth)  
**Scope:** Enterprise Decision Intelligence Platform architecture (pre-code and implementation roadmap phases)  
**Rule:** This file is updated at every approved phase gate.

---

## 1) Architectural Governance

- This is the canonical architecture ledger for the project.
- Previous approved/frozen strategy artifacts remain valid unless a **critical contradiction** is discovered.
- Every new phase must be appended here with:
  1. Purpose
  2. Business rationale
  3. Alternatives considered
  4. Trade-offs
  5. Risks
  6. Failure modes
  7. Validation/Acceptance criteria
  8. Approval status

---

## 2) Frozen Foundations (Approved Inputs)

- Company Vision
- Product Vision
- Business Strategy
- Hidden Problems Research
- Competitor Analysis
- Buying Psychology
- Enterprise Behaviour Graph
- PRD Version 1
- Assumption Falsification
- Value Thesis

---

## 3) Architecture Phase Register

| Phase | Name | Status | Canonical Artifact |
| --- | --- | --- | --- |
| 1 | Enterprise Domains | Approved (conversation) | `PHASE_2_DDD_DOMAIN_DISCOVERY_AND_CONTEXT_MAP.md` |
| 2 | Business Capabilities | Approved | `PHASE_4_BUSINESS_CAPABILITY_MAP_BY_DOMAIN.md` |
| 3 | Bounded Contexts | Approved | `PHASE_5_BOUNDED_CONTEXTS_AND_INTERACTION_CONTRACTS.md` |
| 4 | Enterprise Ontology | Approved | `PHASE_3_EBG_COMPLETE_ONTOLOGY_SPECIFICATION.md` |
| 5 | Enterprise Behaviour Graph | Approved | `ENTERPRISE_BEHAVIOUR_GRAPH_CONCEPTUAL_MODEL.md` |
| 6 | Decision Lifecycle | Approved (within ontology/lifecycles) | `PHASE_3_EBG_COMPLETE_ONTOLOGY_SPECIFICATION.md` |
| 7 | Knowledge Lifecycle | Approved | `PHASE_6_AI_REASONING_ARCHITECTURE_MODEL_AGNOSTIC.md` |
| 8 | Organizational Memory | Approved | `PHASE_6_AI_REASONING_ARCHITECTURE_MODEL_AGNOSTIC.md` |
| 9 | Reasoning Framework | Approved | `PHASE_6_AI_REASONING_ARCHITECTURE_MODEL_AGNOSTIC.md` |
| 10 | Enterprise Events | Approved | `PHASE_3_EBG_COMPLETE_ONTOLOGY_SPECIFICATION.md` |
| 11 | Policies | Pending architecture consolidation | _TBD_ |
| 12 | Business Rules | Approved (core set) | `PHASE_3_EBG_COMPLETE_ONTOLOGY_SPECIFICATION.md` |
| 13 | Trust Architecture | Approved (business level) | `PHASE_5_BOUNDED_CONTEXTS_AND_INTERACTION_CONTRACTS.md` |
| 14 | Economic Value Model | Approved (V1 level) | `PHASE_1_PRD_V1_BUSINESS_OUTCOME.md` |
| 15 | AI Architecture (Conceptual) | Approved (model-agnostic reasoning) | `PHASE_6_AI_REASONING_ARCHITECTURE_MODEL_AGNOSTIC.md` |
| 16 | Plugin Architecture | Pending | _TBD_ |
| 17 | Integration Architecture | Pending | _TBD_ |
| 18 | Multi-Tenant Architecture | Pending | _TBD_ |
| 19 | Deployment Architecture | Pending | _TBD_ |
| 20 | Implementation Roadmap | Pending | _TBD_ |

---

## 4) Current Canonical Architecture Position

### 4.1 Strategic center of gravity
V1 is a **cross-functional decision-accountability wedge** that proves economic value through reduced reversal/rework and attributable outcomes.

### 4.2 Core domains (canonical)
1. Decision Accountability  
2. Outcome Attribution & Value Realization  
3. Cross-Functional Coordination & Dependency Control  
4. Organisational Learning & Decision Memory  
5. Incentive & Behaviour Alignment

### 4.3 Supporting and generic domains
Defined and approved in:
- `PHASE_2_DDD_DOMAIN_DISCOVERY_AND_CONTEXT_MAP.md`
- `PHASE_4_BUSINESS_CAPABILITY_MAP_BY_DOMAIN.md`

### 4.4 Semantic constitution
Canonical ontology, invariants, business rules, lifecycles, events, and transitions are defined in:
- `PHASE_3_EBG_COMPLETE_ONTOLOGY_SPECIFICATION.md`

### 4.5 Reasoning constitution
Model-agnostic enterprise reasoning, confidence, memory, and institutionalization framework is defined in:
- `PHASE_6_AI_REASONING_ARCHITECTURE_MODEL_AGNOSTIC.md`

---

## 5) Living Update Protocol

At each new approved phase, append:
- **Phase ID + Name**
- **Decision summary (what changed/was fixed)**
- **Contradictions discovered (if any)**
- **Accepted architecture decision record (ADR-style short form)**
- **New dependencies introduced**
- **Updated risks/failure modes**

No phase is considered active until recorded here.

---

## 6) Open Architecture Queue

1. Phase 11 consolidation: policy architecture constitution  
2. Phase 16: plugin architecture (business and semantic extension model)  
3. Phase 17: integration architecture (ERP-agnostic context contracts)  
4. Phase 18: multi-tenant architecture (business isolation + learning portability rules)  
5. Phase 19: deployment architecture (cloud-agnostic operating model)  
6. Phase 20: implementation roadmap

---

## 7) Change Log

- **2026-07-27:** Initialized `MASTER_ARCHITECTURE.md` as the project’s single living architecture document and linked approved artifacts.