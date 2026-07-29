# MIGRATION_GUIDE

## Purpose

Document the migration model used by the frozen baseline.

## Patch Model

`patches.txt` uses:
- `[pre_model_sync]` (currently no baseline entries)
- `[post_model_sync]` for deterministic setup after schema sync

Implemented post-model-sync patches:
1. `create_s1_f1_workflow_and_roles`
2. `create_s1_f2_workflow_and_roles`
3. `create_s1_f3_workflow_and_roles`
4. `create_s2_f2_workflow_and_roles`
5. `create_s2_f3_executive_proof_snapshot`

## What patches provision

- Roles (if missing)
- Workflow states (if missing)
- Workflow actions (if missing)
- Workflow definitions and transitions (create/update)
- `Executive Proof Snapshot` Print Format (create/update)

## Idempotency Characteristics

- All patches check existence before insert.
- Existing target artifacts are updated to desired state.
- No duplicate workflow or print format creation on repeated migrate runs.

## Standard Migration Command

```bash
bench --site baby-dokkan.store migrate
```

## Post-migration Verification Checklist

1. `bench migrate` returns success.
2. Workflows are active and state field is `approval_state`.
3. `Executive Proof Snapshot` exists in `Print Format` for `Attribution Case`.
4. Baseline test modules run green.

## What is not part of baseline migration

- No data backfill jobs
- No background migration workers
- No schema changes for Feature 3 (print format only)
