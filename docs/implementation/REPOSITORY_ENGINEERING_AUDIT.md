# REPOSITORY_ENGINEERING_AUDIT

Date: 2026-07-29  
Scope: Repository-wide audit of frozen Sprint 1 + Sprint 2 baseline (no implementation changes)

---

## 1) Executive Summary

- **[Fact]** Baseline implementation surfaces exist and are coherent across DocTypes, controllers, workflows, reports, print format, patches, tests, and documentation.
- **[Fact]** Runtime quality gates executed in this session:
  - `/home/frappe/frappe-bench/env/bin/ruff check .` → pass
  - `bench --site baby-dokkan.store migrate` → pass
  - Baseline regression modules (6 suites) → pass (`18 + 18 + 19 + 21 + 25 + 34` tests; expected conditional skips)
- **[Fact]** No editor diagnostics were reported for the app scope.
- **[Inference]** Current baseline is production-viable for controlled rollout and governance-first operation.
- **[Recommendation]** Approve baseline with targeted maintainability/performance cleanup backlog (non-blocking), preserving freeze constraints.

---

## 2) Architecture Review

### Findings

1. **Governance-centric architecture is consistently implemented**
   - **[Fact]** `Lighthouse Workflow Charter -> Decision Record -> Dependency Exception Record -> Attribution Case` linkage is enforced in controller validation logic and documented in `docs/SYSTEM_ARCHITECTURE.md` and `docs/DOMAIN_MODEL.md`.
   - **[Inference]** Architecture intent and implementation behavior are aligned.

2. **Bounded-context separation is conceptual, not code-partitioned**
   - **[Fact]** `enterprise_intelligence_platform/bounded_contexts/__init__.py` exists as a namespace scaffold only; operational code remains under a single app module tree.
   - **[Inference]** Semantic boundaries are currently enforced by data model and validation, not by package/module isolation.
   - **[Recommendation]** Keep current approach for frozen baseline; if stricter code-level context partitioning is introduced later, treat as incremental refactor and explicitly map migration risk.

3. **Cross-entity governance invariants are repeated across controllers**
   - **[Fact]** `validate_state_transition`, sponsor-gated approval/rejection checks, and approved-record immutability checks appear in all four parent controllers with near-identical patterns.
   - **[Inference]** This duplication increases drift risk across future maintenance.
   - **[Recommendation]** Consolidate shared guard patterns in internal helper utilities without behavior change.

4. **Workflow provisioning architecture is idempotent but duplicated**
   - **[Fact]** `create_s1_f1_workflow_and_roles.py`, `create_s1_f2_workflow_and_roles.py`, `create_s1_f3_workflow_and_roles.py`, `create_s2_f2_workflow_and_roles.py` share largely identical provisioning structure.
   - **[Inference]** Repetition increases maintenance cost and copy/paste defect surface.
   - **[Recommendation]** Introduce a shared internal workflow patch builder for future changes; keep emitted behavior identical.

---

## 3) Code Quality Review

### Findings

1. **Controller quality is strong and readable**
   - **[Fact]** Controller methods are decomposed into focused validation helpers (dates, linkage, state transitions, metadata stamping).
   - **[Inference]** Business-rule readability is high and testability is good.

2. **Moderate duplication exists in test fixture factories**
   - **[Fact]** User/bootstrap fixture builders and charter/decision/dependency construction are repeated across test modules.
   - **[Inference]** This creates change amplification when baseline fixtures evolve.
   - **[Recommendation]** Centralize common fixture builders in a shared test support module (no runtime behavior change).

3. **Naming and rule consistency are generally good**
   - **[Fact]** `approval_state`, sponsor note fields, and metadata fields are consistently used across parent entities.
   - **[Inference]** Consistency reduces operational ambiguity.

---

## 4) Frappe Best Practices Review

### Findings

1. **Strong Frappe-native alignment**
   - **[Fact]** Business rules are server-side in DocType controllers; workflows are native `Workflow` artifacts; reports use Report Builder + Script Report where derived logic is needed.
   - **[Inference]** This is idiomatic and maintainable in Frappe environments.

2. **Idempotent post-model-sync provisioning is correctly used**
   - **[Fact]** Patch modules check existence and update/create roles, workflow states/actions/workflows, and print format.
   - **[Inference]** Deploy/re-run safety is appropriately designed.

3. **Permission model is role-scoped and explicit**
   - **[Fact]** Parent DocTypes and reports include expected roles (`System Manager`, `EIP Workflow Owner`, `EIP Executive Sponsor`, `EIP Operations Manager`).
   - **[Inference]** Access model is straightforward and auditable.

4. **No unsafe custom API surface observed**
   - **[Fact]** No active whitelisted methods, guest endpoints, or custom permission bypass APIs were found in app hooks.
   - **[Inference]** API attack surface in this baseline is minimal.

---

## 5) Performance Review

### Findings

1. **Script report query design is good**
   - **[Fact]** `operational_review_view.py` uses Query Builder joins and grouped aggregate query for open exception counts.
   - **[Inference]** Report avoids obvious row-by-row query anti-patterns in core data fetch path.

2. **Print format contains N+1 lookup pattern**
   - **[Fact]** `create_s2_f3_executive_proof_snapshot.py` Jinja loops perform per-row `frappe.db.exists` / `frappe.get_doc` on dependency references.
   - **[Inference]** Render cost grows with attribution chain size.
   - **[Recommendation]** Keep as accepted debt in frozen baseline; optimize only when observed latency justifies change.

3. **Attribution validation may perform repeated DB reads per chain step**
   - **[Fact]** `AttributionCase.validate_chain_steps()` queries dependency decision linkage per row.
   - **[Inference]** For large chain tables, save-time DB calls scale linearly.
   - **[Recommendation]** Future optimization could prefetch referenced dependencies in one query if evidence shows save latency issues.

---

## 6) Security Review

### Findings

1. **Approval authorization is enforced in workflow + controller layers**
   - **[Fact]** Workflow transition conditions require designated sponsor; controllers enforce sponsor-only transitions and rejection-note requirements.
   - **[Inference]** Dual-layer checks reduce accidental misconfiguration risk.

2. **Immutability controls are explicit**
   - **[Fact]** Approved/accepted records are blocked from mutation for non-`System Manager` users across controllers.
   - **[Inference]** Post-approval integrity is strong for normal save paths.

3. **Permission enforcement exists for operational report and print rendering**
   - **[Fact]** Script report checks read permission; tests verify disallowed users fail. Print tests verify unauthorized rendering fails.
   - **[Inference]** Read-path authorization behavior is validated.

4. **Known trusted-path bypass caveat exists (`db_set`)**
   - **[Fact]** Repository docs explicitly note `db_set()` bypasses controller validation by Frappe design.
   - **[Inference]** Security posture depends on limiting trusted internal usage of low-level write paths.
   - **[Recommendation]** Keep this caveat documented and avoid introducing service paths that rely on `db_set()` for business transitions.

5. **Privilege-escalation hotspots not found in app code**
   - **[Fact]** No `allow_guest=True` endpoints or active custom whitelisted methods were found.
   - **[Inference]** Direct app-level escalation surface is low.

---

## 7) Documentation Review

### Findings

1. **Core baseline docs align well with implementation**
   - **[Fact]** `SYSTEM_ARCHITECTURE.md`, `DOMAIN_MODEL.md`, `GOVERNANCE_MODEL.md`, `WORKFLOW_GUIDE.md`, `REPORT_GUIDE.md`, `MIGRATION_GUIDE.md`, `TESTING_GUIDE.md` reflect implemented artifacts and behaviors.
   - **[Inference]** Core operational documentation quality is strong.

2. **Freeze policy is clearly documented**
   - **[Fact]** Sprint freeze constraints appear consistently across implementation package and governance docs.
   - **[Inference]** Change governance expectations are explicit.

3. **Backlog status document has historical drift risk**
   - **[Fact]** `docs/implementation/SPRINT_1_BACKLOG_STATUS.md` still lists `S1-F4/S1-F5/S1-F6` as planned/not started, while those capabilities exist in baseline as Sprint 2 implemented scope.
   - **[Inference]** Readers may misinterpret implementation maturity if they use this file as current status truth.
   - **[Recommendation]** Mark it as historical snapshot or add explicit superseded note linking to Sprint 2 completion package.

4. **ADR formalization is partial but traceability exists**
   - **[Fact]** One formal ADR file exists (`ADR-0001`) and additional architecture decisions are captured in `docs/ARCHITECTURAL_DECISIONS.md`.
   - **[Inference]** Decision trace exists, though split across ADR and non-ADR documents.

---

## 8) Test Quality Review

### Findings

1. **Coverage breadth is strong for baseline behavior**
   - **[Fact]** Tests cover validation rules, state transitions, permission errors, report filters/derived fields, print format gating/content/order, and regression for `supports_claim` normalization.
   - **[Inference]** High confidence for baseline business invariants.

2. **Runtime behavior alignment is actively considered**
   - **[Fact]** Workflow tests conditionally skip native `apply_workflow` checks when environment monkey patches are detected.
   - **[Inference]** Test suite acknowledges environment variance while still validating controller invariants.

3. **Gap: explicit patch idempotency tests are limited**
   - **[Fact]** Idempotency is validated indirectly via repeated migrate execution and docs; dedicated unit tests for each patch idempotency path are not prominent.
   - **[Inference]** Coverage is practical but could be tightened for patch regressions.
   - **[Recommendation]** Add focused patch idempotency tests when modifying patch framework in future.

4. **Gap: shared fixture abstraction is minimal**
   - **[Fact]** Fixture setup logic repeats heavily across modules.
   - **[Inference]** Maintenance burden can grow with additional suites.
   - **[Recommendation]** Introduce shared fixture helpers (non-behavioral refactor).

---

## 9) Technical Debt Register (Prioritized)

### Critical
- **None evidenced in current frozen baseline.**

### High
1. **Workflow patch duplication across four modules**
   - **[Fact]** Near-identical role/state/action/workflow provisioning logic is repeated.
   - **[Inference]** High drift risk when one workflow contract changes.
   - **[Recommendation]** Refactor to shared internal provisioning helper (behavior-preserving).

2. **Controller governance guard duplication**
   - **[Fact]** Similar transition/immutability/sponsor checks are repeated in each parent controller.
   - **[Inference]** Rule divergence risk increases over time.
   - **[Recommendation]** Extract common validation primitives with strict regression tests.

### Medium
3. **Executive Proof Snapshot per-row dependency lookups (N+1 style)**
   - **[Fact]** Per-chain row existence/doc fetch inside Jinja render loop.
   - **[Inference]** Scales linearly with chain size; may impact render latency at volume.
   - **[Recommendation]** Optimize only when latency thresholds are exceeded.

4. **Attribution chain validation repeated DB access per row**
   - **[Fact]** `validate_chain_steps` resolves dependency decision linkage row-by-row.
   - **[Inference]** Potential save-time overhead at high row counts.
   - **[Recommendation]** Consider prefetch path when evidence warrants.

5. **Documentation status drift (`SPRINT_1_BACKLOG_STATUS.md`)**
   - **[Fact]** Contains now-outdated planned/not-started statements for capabilities implemented in Sprint 2.
   - **[Inference]** Risk of stakeholder confusion.
   - **[Recommendation]** Mark historical or superseded.

### Low
6. **README install branch guidance may be stale**
   - **[Fact]** Root README install snippet references `--branch develop` while current repository context is `main`.
   - **[Inference]** Potential onboarding confusion.
   - **[Recommendation]** Align README branch guidance with active branch policy.

7. **Test fixture boilerplate duplication**
   - **[Fact]** Repeated user and document fixture factory logic across suites.
   - **[Inference]** Low immediate risk, but ongoing maintenance overhead.
   - **[Recommendation]** Consolidate fixtures over time.

---

## 10) ADR Recommendations

### ADR required only if behavior/contracts change

1. **Workflow/state-semantic change on frozen entities**
   - **[Recommendation]** Any change to `approval_state` lifecycle semantics requires ADR.

2. **Permission model relaxation/tightening that changes user capabilities**
   - **[Recommendation]** Role permission contract changes require ADR.

3. **Immutability policy changes for approved/accepted records**
   - **[Recommendation]** Any relaxation or stricter mutation policy requires ADR.

4. **Source-of-truth model changes (e.g., persisted snapshot entity)**
   - **[Recommendation]** Introducing duplicate persistence for proof artifacts requires ADR.

### No ADR required for pure non-behavioral maintenance

- **[Recommendation]** Internal refactors that preserve behavior (shared patch helper, shared validation helpers, shared test fixtures) can proceed without ADR, provided regression suite remains green.

---

## 11) Overall Scores

- **Architecture:** **8.2 / 10**  
  - **[Fact]** Coherent governance-centric model with implemented cross-entity integrity.
- **Security:** **8.5 / 10**  
  - **[Fact]** Strong server-side validations + role/workflow gates + low API surface.
- **Maintainability:** **7.4 / 10**  
  - **[Fact]** Clear code structure, but notable duplication in controllers/patches/tests.
- **Test Quality:** **8.6 / 10**  
  - **[Fact]** Broad behavior coverage and successful runtime verification.
- **Documentation:** **7.9 / 10**  
  - **[Fact]** Strong core docs with minor status drift in historical backlog document.
- **Production Readiness:** **8.4 / 10**  
  - **[Fact]** Lint + migrate + baseline regression suites passed in current session.

---

## 12) Final Recommendation

## **APPROVE CURRENT BASELINE**

- **[Fact]** No blocker-level defects were evidenced during repository-wide audit.
- **[Inference]** Frozen Sprint 1 + Sprint 2 baseline is stable, governed, and release-ready for controlled operation.
- **[Recommendation]** Track listed debt items in prioritized backlog; keep behavior-preserving improvements non-invasive, and route any contract-changing proposal through ADR first.
