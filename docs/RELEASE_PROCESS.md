# RELEASE_PROCESS

## Release Model for Frozen Baseline

Sprint 1 + Sprint 2 are frozen contracts. Releases must preserve backward compatibility.

## Release Stages

1. **Implementation complete**
2. **Independent review** (source + runtime)
3. **Quality gates** (lint, migrate, tests)
4. **Freeze decision**
5. **Rollout tier decision**

## Quality Gate Checklist

- [ ] `ruff check .` passes
- [ ] `bench migrate` passes
- [ ] Changed feature suites pass
- [ ] Frozen baseline regression suites pass
- [ ] No unresolved blocking findings

## Regression Set (Baseline)

- `test_lighthouse_workflow_charter`
- `test_decision_record`
- `test_dependency_exception_record`
- `test_operational_review_view`
- `test_attribution_case`
- `test_executive_proof_snapshot`

## Freeze Policy

- Baseline change requires:
  - reproducible production defect **or**
  - approved architecture decision

## Recommended Current Rollout Tier

Based on validated baseline evidence in Sprint 2 package:
- **Pilot customers** (controlled rollout)

## Documentation Requirements for each release

- Completion package with:
  - artifact summary
  - quality outcomes
  - technical debt register (non-blocking only)
  - freeze record
  - release recommendation

## Required Release Attachments (`v0.2.0-baseline`)

- Sprint 2 Completion Package (`docs/implementation/SPRINT_2_COMPLETION_PACKAGE.md`)
- Repository Engineering Audit (`docs/implementation/REPOSITORY_ENGINEERING_AUDIT.md`)
- Release Readiness Review (`docs/implementation/V0_2_0_RELEASE_READINESS.md`)
- Technical Debt (`docs/TECHNICAL_DEBT.md`)
- Known Limitations (`docs/KNOWN_LIMITATIONS.md`)
- Rollback Note (release attachment)

## Rollback Procedure (Documentation)

If rollback is required after tagging/release:

1. Restore previous stable release tag in the deployment target.
2. Run `bench --site <site> migrate`.
3. Run baseline regression suites:
  - `test_lighthouse_workflow_charter`
  - `test_decision_record`
  - `test_dependency_exception_record`
  - `test_operational_review_view`
  - `test_attribution_case`
  - `test_executive_proof_snapshot`
4. Verify application startup and operational access.
