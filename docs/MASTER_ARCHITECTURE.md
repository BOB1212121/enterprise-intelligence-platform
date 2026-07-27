# MASTER_ARCHITECTURE.md

**Status:** Living document (single source of architectural truth)  
**Scope:** Enterprise Decision Intelligence Platform architecture (pre-code and implementation roadmap phases)  
**Rule:** This file is updated at every approved phase gate.

> **Canonical source note (Sprint 0):** `docs/MASTER_ARCHITECTURE.md` is the canonical architecture source for implementation governance.

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
- Engineering Constitution

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
| 16 | Engineering Constitution | Approved | `ENGINEERING_CONSTITUTION.md` |
| 17 | Reference Architecture | Draft for approval (Sprint 0 / S0-F1) | `docs/Architecture/REFERENCE_ARCHITECTURE.md` |
| 18 | Plugin Architecture | Pending | _TBD_ |
| 19 | Integration Architecture | Pending | _TBD_ |
| 20 | Multi-Tenant Architecture | Pending | _TBD_ |
| 21 | Security Architecture | Pending | _TBD_ |
| 22 | Deployment Architecture | Pending | _TBD_ |
| 23 | DevOps Architecture | Pending | _TBD_ |
| 24 | Implementation Roadmap | Pending | _TBD_ |

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
2. Phase 17: reference architecture (canonical engineering blueprint)  
3. Phase 18: plugin architecture (business and semantic extension model)  
4. Phase 19: integration architecture (ERP-agnostic context contracts)  
5. Phase 20: multi-tenant architecture (business isolation + learning portability rules)  
6. Phase 21: security architecture (trust, control, and governance model)  
7. Phase 22: deployment architecture (cloud-agnostic operating model)  
8. Phase 23: DevOps architecture (delivery governance and operational lifecycle)  
9. Phase 24: implementation roadmap

**Execution rule (Sprint 0 onward):** Once Phase 17 (`docs/Architecture/REFERENCE_ARCHITECTURE.md`) is approved, implementation proceeds immediately; no further architecture document blocks execution unless a critical contradiction is discovered and logged via ADR.

---

## 7) Engineering Architecture Authority

- Canonical engineering authority document: `ENGINEERING_CONSTITUTION.md`
- This constitution governs all engineering and architecture decisions unless superseded by law, mission-level governance, or explicitly approved constitutional amendment.
- All future architecture phases must reference constitutional compliance in their acceptance criteria.

---

## 8) Change Log

- **2026-07-27:** Initialized `MASTER_ARCHITECTURE.md` as the project’s single living architecture document and linked approved artifacts.
- **2026-07-27:** Added `ENGINEERING_CONSTITUTION.md` as highest engineering authority and transitioned architecture governance into Engineering Architecture mode.
- **2026-07-27:** Reordered remaining engineering phases: Engineering Constitution -> Reference Architecture -> Plugin -> Integration -> Multi-Tenant -> Security -> Deployment -> DevOps -> Implementation Roadmap.
- **2026-07-27:** Added Sprint 0 Reference Architecture draft (`docs/Architecture/REFERENCE_ARCHITECTURE.md`) and ADR-0001; established non-blocking implementation rule after Phase 17 approval unless critical contradiction is logged.
- **2026-07-27:** Implementation progress — S1-F1 completed (Lighthouse Workflow Setup & Baseline Charter) on `baby-dokkan.store` with Frappe-native DocTypes, Workflow, permissions, report, validations, and passing test suite. External workflow monkey-patch incompatibility documented as non-app issue.
- **2026-07-27:** Implementation progress — S1-F2 completed (Decision Record with Accountability & Assumptions) on `baby-dokkan.store` with Frappe-native workflow governance, server-side validations, report, and passing test suite.
- **2026-07-27:** Implementation progress — S1-F3 completed (Dependency & Exception Tracking) on `baby-dokkan.store` with Frappe-native dependency/exception record workflow, validations, report, and passing test suite.