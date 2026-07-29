> **Status: Historical / Superseded**
>
> Implementation status is maintained in:
> `docs/implementation/SPRINT_2_COMPLETION_PACKAGE.md`

# Sprint 1 Backlog & Status

## Sprint policy
- Product implementation mode.
- One feature at a time with review gates.

## Backlog status

| Feature | Title | Status | Notes |
| --- | --- | --- | --- |
| S1-F1 | Lighthouse Workflow Setup & Baseline Charter | **Completed** | Closed with production-readiness audit and app-owned hardening. |
| S1-F2 | Decision Record with Accountability & Assumptions | **Completed** | Closed with hardening pass and quality gates. |
| S1-F3 | Dependency & Exception Tracking | **Completed** | Implemented Frappe-native dependency + exception record workflow and test suite. |
| S1-F4 | Operational Review View | Planned | Not started. |
| S1-F5 | Attribution Chain & Confidence Entry | Planned | Not started. |
| S1-F6 | Executive Proof Snapshot | Planned | Not started. |

---

## S1-F1 close-out (frozen)

### Objective achieved
Establish a customer-visible lighthouse workflow charter baseline with Frappe-native governance so one workflow can be scoped, measured, and sponsor-approved.

### Implemented functionality
- DocType: `Lighthouse Workflow Charter`
- Child Table: `Lighthouse Baseline KPI`
- Workflow: `Lighthouse Workflow Charter Approval` (all states at `docstatus=0`)
- Roles: `EIP Workflow Owner`, `EIP Executive Sponsor`, `EIP Operations Manager`
- Report Builder report: `Lighthouse Workflow Charter Register`
- Server-side validations for KPI set integrity, date rules, sponsor-only approval/rejection, acceptance metadata, and accepted-record immutability for non-System Managers
- Automated S1-F1 tests

### Acceptance criteria checklist
- [x] Workflow charter can be created with required owner/sponsor/scope fields
- [x] Required baseline KPI set enforced (`DRR`, `DCT`, `AER`, `OCR`, `RER`)
- [x] Sponsor approval/rejection state logic enforced
- [x] Rejection requires decision note
- [x] Baseline acceptance metadata captured (`accepted_by`, `accepted_on`)
- [x] Accepted records immutable for non-System Managers
- [x] Register report available with expected columns and role access
- [x] Automated tests pass on target site

### Test summary
- Site: `baby-dokkan.store`
- Test module: `enterprise_intelligence_platform.enterprise_intelligence_platform.doctype.lighthouse_workflow_charter.test_lighthouse_workflow_charter`
- Last run result: `Ran 18 tests` → `OK (skipped=1)`

### Known limitations
- Native `frappe.model.workflow.apply_workflow` regression test is conditionally skipped when environment-level workflow monkey patches are detected.

### Technical debt
- None blocking inside Enterprise Intelligence Platform for S1-F1.

### Open risks
- External compatibility risk if third-party apps monkey-patch workflow internals against outdated schema assumptions.

### Deployment notes
1. Run: `bench --site baby-dokkan.store migrate`
2. Ensure tests are enabled for CI/site validation: `allow_tests = true`
3. Run S1-F1 module tests before release gate.

### Lessons learned (implementation guidelines)
- Prefer native Frappe Workflow + Role Permission patterns before adding Python logic.
- Place business data-integrity rules in DocType controller `validate()`; avoid service-layer indirection for simple invariants.
- Use workflow transition conditions for role/state gating and keep server-side guards for critical integrity (e.g., immutable accepted records).
- Keep tests at DocType behavior level (validation, transition permissions, immutability).
- Add conditional workflow regression tests that detect patched environments without introducing app-side workarounds.
- Avoid dependencies on third-party monkey-patched internals; treat those as external compatibility boundaries.

---

## S1-F3 close-out (frozen)

### Objective achieved
Establish dependency and exception tracking tied to decision accountability so blocker visibility, exception discipline, and sponsor governance are auditable in a Frappe-native workflow.

### Implemented functionality
- DocType: `Dependency Exception Record`
- Workflow: `Dependency Exception Record Approval` (all states at `docstatus=0`)
- Roles: `EIP Workflow Owner`, `EIP Executive Sponsor`, `EIP Operations Manager`
- Report Builder report: `Dependency Exception Record Register`
- Server-side validations for decision linkage integrity, date rules, exception mandatory fields, resolved-state note requirement, sponsor-only approval/rejection, rejection note requirement, approval metadata, and approved-record immutability for non-System Managers
- Automated S1-F3 tests

### Acceptance criteria checklist
- [x] Dependency record can be created with required linkage, owner/sponsor, and dependency fields
- [x] Decision linkage integrity enforced (sponsor/charter must align to linked `Decision Record`)
- [x] Date rules enforced for resolution and exception expiry
- [x] Exception governance fields required when exception flag is enabled (owner/reason/expiry/remediation intent)
- [x] Resolved status requires resolution note
- [x] Sponsor approval/rejection state logic enforced
- [x] Rejection requires sponsor decision note
- [x] Approval metadata captured (`approved_by`, `approved_on`)
- [x] Approved records immutable for non-System Managers
- [x] Register report available with expected columns and role access

### Test summary
- Site: `baby-dokkan.store`
- Test module: `enterprise_intelligence_platform.enterprise_intelligence_platform.doctype.dependency_exception_record.test_dependency_exception_record`
- Last run result: `Ran 19 tests` → `OK (skipped=1)`

### Known limitations
- Native `frappe.model.workflow.apply_workflow` regression test is conditionally skipped when environment-level workflow monkey patches are detected.

### Technical debt
- None blocking inside Enterprise Intelligence Platform for S1-F3.

### Open risks
- External compatibility risk remains if third-party apps monkey-patch workflow internals against outdated schema assumptions.

### Developer note (workflow integrity boundary)
- Sprint 1 workflow integrity guards are enforced in controller `validate()` and native workflow actions, i.e. `insert()/save()/apply_workflow` paths.
- `db_set()` bypasses controller validation by design in Frappe and must only be used by trusted internal code paths.

### Deployment notes
1. Run: `bench --site baby-dokkan.store migrate`
2. Ensure tests are enabled for CI/site validation: `allow_tests = true`
3. Run S1-F3 module tests before release gate.
