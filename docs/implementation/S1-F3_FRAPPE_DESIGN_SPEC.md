# S1-F3 Frappe Design Spec (Implemented)

This file records the approved and implemented S1-F3 scope in Frappe-native form.

## Scope
- Dependency and exception tracking DocType linked to `Decision Record`.
- Native Workflow-driven sponsor approval (docstatus remains 0).
- Role-based access using standard DocType permissions + Workflow transition rules.
- Report Builder register for operational visibility.
- Minimal server-side validations in the DocType controller.
- Automated tests.

## Implemented artifacts
- DocType: `Dependency Exception Record`
- Workflow: `Dependency Exception Record Approval`
- Patch: `create_s1_f3_workflow_and_roles`
- Report Builder report: `Dependency Exception Record Register`
- Test module: `test_dependency_exception_record.py`

## Core validations
- Decision linkage integrity (`decision_record` must resolve and sponsor/charter must match linked decision)
- Date rules (`target_resolution_date >= declaration_date`, exception expiry cannot precede declaration)
- Exception discipline (when exception is required, owner/reason/expiry/remediation intent are mandatory)
- Resolved-state discipline (resolution note required when status is `Resolved`)
- Sponsor-only approval/rejection enforcement
- Rejection-note requirement
- Approved-record immutability for non-System Managers
- Approval metadata stamping (`approved_by`, `approved_on`)

## Explicit exclusions
- No client scripts
- No custom APIs
- No hooks
- No future-sprint capabilities
