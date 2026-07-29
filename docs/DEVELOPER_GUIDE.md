# DEVELOPER_GUIDE

## Audience

Senior Frappe developers onboarding to the frozen Sprint 1 + Sprint 2 baseline.

## Repository Layout (Implemented)

- App root: `apps/enterprise_intelligence_platform`
- Domain models:
  - `enterprise_intelligence_platform/doctype/lighthouse_workflow_charter/`
  - `enterprise_intelligence_platform/doctype/decision_record/`
  - `enterprise_intelligence_platform/doctype/dependency_exception_record/`
  - `enterprise_intelligence_platform/doctype/attribution_case/`
- Child tables:
  - `lighthouse_baseline_kpi`, `decision_assumption`, `attribution_chain_step`, `attribution_evidence`
- Reports:
  - `report/*_register/*.json` (Report Builder)
  - `report/operational_review_view/*` (Script Report)
- Patch provisioning:
  - `patches/post_model_sync/*.py`
  - `patches.txt`

## Baseline Rules

1. Sprint 1 + Sprint 2 are frozen baseline.
2. Do not modify baseline contracts unless:
   - reproducible production defect, or
   - approved architecture decision.
3. Prefer additive, backward-compatible changes.

## Development Patterns in Baseline

- Controller-centric invariants in `validate()`
- Workflow-state integrity checks in controllers (server-side)
- Idempotent post-model-sync patch setup
- Role-scoped reports and print outputs

## Commands Used in Baseline

```bash
bench --site baby-dokkan.store migrate
bench --site baby-dokkan.store run-tests --module enterprise_intelligence_platform.enterprise_intelligence_platform.doctype.lighthouse_workflow_charter.test_lighthouse_workflow_charter
bench --site baby-dokkan.store run-tests --module enterprise_intelligence_platform.enterprise_intelligence_platform.doctype.decision_record.test_decision_record
bench --site baby-dokkan.store run-tests --module enterprise_intelligence_platform.enterprise_intelligence_platform.doctype.dependency_exception_record.test_dependency_exception_record
bench --site baby-dokkan.store run-tests --module enterprise_intelligence_platform.enterprise_intelligence_platform.doctype.attribution_case.test_attribution_case
bench --site baby-dokkan.store run-tests --module enterprise_intelligence_platform.enterprise_intelligence_platform.report.operational_review_view.test_operational_review_view
bench --site baby-dokkan.store run-tests --module enterprise_intelligence_platform.enterprise_intelligence_platform.doctype.attribution_case.test_executive_proof_snapshot
ruff check .
```

## How to Add Safe Changes (Future, after approval)

1. Add/adjust schema (`.json`) only if strictly required.
2. Keep business invariants in controller `validate()`.
3. Add/adjust post-model-sync patch idempotently.
4. Add regression tests for new or changed behavior.
5. Re-run frozen baseline suites.

## Implemented Extension Boundary

- No custom APIs/hook-based orchestration introduced for Sprint 1/2.
- No background workers required for baseline capabilities.
- Rendering logic for Feature 3 lives in print format provisioning patch.
