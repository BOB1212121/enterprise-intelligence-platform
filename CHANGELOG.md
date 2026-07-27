# Changelog

All notable changes to this app are documented in this file.

## 2026-07-27

### Added — S0-F1 foundation guardrails
- Minimal bounded-context namespace scaffold.
- Baseline test package and CI workflow.
- Canonical architecture source note usage in `docs/MASTER_ARCHITECTURE.md`.

### Added — S1-F1 lighthouse baseline charter
- DocType: `Lighthouse Workflow Charter`.
- Child Table: `Lighthouse Baseline KPI`.
- Workflow: `Lighthouse Workflow Charter Approval`.
- Roles and permissions for owner/sponsor/operations manager.
- Report Builder report: `Lighthouse Workflow Charter Register`.
- Server-side validations for KPI integrity, sponsor transitions, rejection note, acceptance metadata, and accepted-record immutability.
- Automated test suite for S1-F1 validations and workflow-related behavior.

### Added — S1-F2 decision accountability record
- DocType: `Decision Record`.
- Child Table: `Decision Assumption`.
- Workflow: `Decision Record Approval`.
- Report Builder report: `Decision Record Register`.
- Server-side validations for charter/sponsor linkage integrity, assumption quality constraints, sponsor transitions, rejection note, approval metadata, and approved-record immutability.
- Automated test suite for S1-F2 validations and workflow-related behavior.

### Added — S1-F3 dependency & exception tracking
- DocType: `Dependency Exception Record`.
- Workflow: `Dependency Exception Record Approval`.
- Report Builder report: `Dependency Exception Record Register`.
- Server-side validations for decision linkage integrity, dependency/exception date rules, mandatory exception controls, sponsor transitions, rejection note, approval metadata, and approved-record immutability.
- Automated test suite for S1-F3 validations and workflow-related behavior.

### Changed
- Consolidated S1-F1 artifacts into a single canonical implementation tree under `enterprise_intelligence_platform/enterprise_intelligence_platform/`.

### Known external compatibility note
- Workflow runtime failures involving `wt.required_fields` are external to this app and traced to third-party workflow monkey patches (`syarahconnector`) expecting non-native schema columns.
