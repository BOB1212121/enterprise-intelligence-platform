# TROUBLESHOOTING

## 1) Workflow transition fails unexpectedly

### Symptom
- `WorkflowPermissionError` or transition rejected.

### Checks
1. Confirm user role (`Workflow Owner` vs `Executive Sponsor` vs `System Manager`).
2. Confirm transition condition fields are populated (e.g., rejection note).
3. Confirm target record has correct `executive_sponsor`.
4. Confirm active workflow is correct for target DocType.

### Notes
- In some environments, workflow internals may be monkey-patched by other apps.

## 2) Report execution denied

### Symptom
- `PermissionError` when running `Operational Review View`.

### Checks
1. User has read access to `Dependency Exception Record`.
2. Report role includes user role.
3. Site migration applied latest report metadata.

## 3) Executive Proof Snapshot render blocked

### Expected behavior
- Snapshot only renders when `Attribution Case.approval_state == Approved`.

### If blocked unexpectedly
1. Verify current state is exactly `Approved`.
2. Verify linked `Decision Record` and `Lighthouse Workflow Charter` exist.
3. Verify linked dependency references in chain rows resolve.
4. Verify user has read/print permission for attribution case.

## 4) supports_claim validation errors

### Symptom
- Evidence row fails with `Supports Claim must be either 0 or 1.`

### Accepted values
- `0`, `1`, `"0"`, `"1"`, `False`, `True`

### Invalid values
- Arbitrary strings and non-binary integers.

## 5) Patch-related migrate failures

### Symptom
- Error during `bench migrate` in post-model-sync phase.

### Checks
1. Confirm patch path is listed once in `patches.txt`.
2. Confirm patch is idempotent and handles existing records.
3. Confirm required Frappe DocTypes (`Workflow`, `Print Format`) are available.

## 6) Baseline regression safety check

When in doubt before release:
1. Run `ruff check .`
2. Run `bench migrate`
3. Run all baseline test modules
4. Re-verify no blocking findings
