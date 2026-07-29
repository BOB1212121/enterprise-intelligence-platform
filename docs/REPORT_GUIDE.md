# REPORT_GUIDE

## Implemented Reporting Artifacts

### Report Builder Registers
- `Lighthouse Workflow Charter Register`
- `Decision Record Register`
- `Dependency Exception Record Register`
- `Attribution Case Register`

All register reports are role-scoped to:
- `System Manager`
- `EIP Workflow Owner`
- `EIP Executive Sponsor`
- `EIP Operations Manager`

### Script Report
- `Operational Review View`
  - Ref DocType: `Dependency Exception Record`
  - Backed by:
    - `operational_review_view.py`
    - `operational_review_view.js`
    - `operational_review_view.json`

## Operational Review View Behavior

- Permission gate: requires read on `Dependency Exception Record`
- Supports filters for sponsor/owner/charter/decision/state/status/criticality/exception/date range
- Derived indicators:
  - `pending_sponsor_action`
  - `overdue_flag`
  - `at_risk_flag`
  - `open_exceptions_count`
- Deterministic sort key: target date, criticality rank, dependency name

## Filter Semantics Note

`exception_required` uses normalized tri-state handling from script report logic:
- empty => no filter
- Yes/1/true => `1`
- No/0/false => `0`

## Print Artifact in Reporting Context

- `Executive Proof Snapshot` is implemented as a Print Format (not a Report).
- It is approved-state gated and role-constrained via document read/print permissions.

## Testing

- `test_operational_review_view.py` validates filter behavior, derived fields, deterministic ordering, and permission enforcement.
