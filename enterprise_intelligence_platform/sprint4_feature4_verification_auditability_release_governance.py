from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, getdate, now_datetime

GOVERNANCE_ROLES = (
	"EIP Workflow Owner",
	"EIP Executive Sponsor",
	"EIP Operations Manager",
	"System Manager",
)

S4F4_AUDIT_LOGGER_NAME = "enterprise_intelligence_platform.sprint4_feature4"

GO = "GO"
DEFER = "DEFER"
NO_GO = "NO-GO"

MANDATORY_EVIDENCE_FIELDS = (
	"scope_declaration",
	"baseline_preservation_statement",
	"additive_only_statement",
	"contract_preservation_statement",
	"gate_assessment_record",
	"approval_authority_record",
	"security_boundary_confirmation",
	"operational_safety_record",
	"traceability_audit_record",
	"validation_replay_record",
	"release_governance_record",
)

DEFER_BLOCKER_TYPE_FIELD = "defer_blocker_type"
DEFER_BLOCKER_REFERENCE_FIELD = "defer_blocker_reference"

MUTATION_INDICATOR_FIELDS = (
	"modifies_workflow_semantics",
	"changes_approval_state_semantics",
	"changes_permission_authority",
	"changes_ownership_or_source_of_truth",
	"changes_immutability_behavior",
	"changes_baseline_authoritative_persistence",
	"mutates_approved_feature_contracts",
)

APPROVED_VALUE_SET = {"approved", "yes", "true", "1", "confirmed", "pass", "validated"}
REJECTED_VALUE_SET = {"rejected", "no", "false", "0"}
TRUTHY_VALUE_SET = APPROVED_VALUE_SET

DEFER_BLOCKER_ALLOWED = {"external_dependency", "scheduled_governance_activity"}


@dataclass(frozen=True)
class Sprint4Feature4GovernanceContext:
	evidence_package: dict[str, Any]
	mutation_indicators: dict[str, int]
	governance_rationale: str


@dataclass(frozen=True)
class Sprint4Feature4GovernanceItem:
	lighthouse_workflow_charter: str
	decision_record: str
	review_window_start: str
	review_window_end: str
	policy_version: str
	readiness_outcome: str
	implementation_authorized: int
	adr_route_required: int
	baseline_change_trigger_detected: int
	evidence_completeness_pct: float
	rg_001_evidence_completeness_pass: int
	rg_002_additive_conformance_pass: int
	rg_003_security_boundary_pass: int
	rg_004_mandatory_approvals_pass: int
	rg_005_release_governance_integrity_pass: int
	rg_006_rollback_readiness_pass: int
	rg_007_incident_response_readiness_pass: int
	rg_008_recovery_readiness_pass: int
	rg_009_operational_verification_pass: int
	rg_010_monitoring_observability_pass: int
	rg_011_release_governance_readiness_pass: int
	rg_012_traceability_audit_pass: int
	gate_1_pass: int
	gate_2_pass: int
	gate_3_pass: int
	gate_4_pass: int
	gate_5_pass: int
	gate_sequence_passed: int
	governance_role_confirmed: int
	read_only_confirmed: int
	ranking_rationale: str

	def as_dict(self) -> dict[str, Any]:
		return {
			"lighthouse_workflow_charter": self.lighthouse_workflow_charter,
			"decision_record": self.decision_record,
			"review_window_start": self.review_window_start,
			"review_window_end": self.review_window_end,
			"policy_version": self.policy_version,
			"readiness_outcome": self.readiness_outcome,
			"implementation_authorized": self.implementation_authorized,
			"adr_route_required": self.adr_route_required,
			"baseline_change_trigger_detected": self.baseline_change_trigger_detected,
			"evidence_completeness_pct": self.evidence_completeness_pct,
			"rg_001_evidence_completeness_pass": self.rg_001_evidence_completeness_pass,
			"rg_002_additive_conformance_pass": self.rg_002_additive_conformance_pass,
			"rg_003_security_boundary_pass": self.rg_003_security_boundary_pass,
			"rg_004_mandatory_approvals_pass": self.rg_004_mandatory_approvals_pass,
			"rg_005_release_governance_integrity_pass": self.rg_005_release_governance_integrity_pass,
			"rg_006_rollback_readiness_pass": self.rg_006_rollback_readiness_pass,
			"rg_007_incident_response_readiness_pass": self.rg_007_incident_response_readiness_pass,
			"rg_008_recovery_readiness_pass": self.rg_008_recovery_readiness_pass,
			"rg_009_operational_verification_pass": self.rg_009_operational_verification_pass,
			"rg_010_monitoring_observability_pass": self.rg_010_monitoring_observability_pass,
			"rg_011_release_governance_readiness_pass": self.rg_011_release_governance_readiness_pass,
			"rg_012_traceability_audit_pass": self.rg_012_traceability_audit_pass,
			"gate_1_pass": self.gate_1_pass,
			"gate_2_pass": self.gate_2_pass,
			"gate_3_pass": self.gate_3_pass,
			"gate_4_pass": self.gate_4_pass,
			"gate_5_pass": self.gate_5_pass,
			"gate_sequence_passed": self.gate_sequence_passed,
			"governance_role_confirmed": self.governance_role_confirmed,
			"read_only_confirmed": self.read_only_confirmed,
			"ranking_rationale": self.ranking_rationale,
		}


def evaluate_sprint4_feature4_verification_auditability_release_governance(
	*,
	lighthouse_workflow_charter: str,
	review_window_start: str,
	review_window_end: str,
	policy_version: str,
	decision_record: str | None = None,
	governance_context: dict[str, Any] | None = None,
	invocation_context: str = "direct_helper_call",
) -> tuple[Sprint4Feature4GovernanceItem, ...]:
	_require_governance_role()
	_require_read_permissions()

	window_start, window_end = _validate_review_window(review_window_start, review_window_end)
	policy_version_text = _normalize_required_text(policy_version, "Policy Version")
	context = _resolve_governance_context(governance_context)

	decision_rows = _fetch_decision_docs(lighthouse_workflow_charter, decision_record)
	items: list[Sprint4Feature4GovernanceItem] = []
	for decision in decision_rows:
		items.append(
			_build_item(
				decision=decision,
				window_start=window_start,
				window_end=window_end,
				policy_version=policy_version_text,
				context=context,
			)
		)

	sorted_items = tuple(sorted(items, key=_item_sort_key))
	_record_actor_trace_audit_evidence(
		invocation_context=invocation_context,
		lighthouse_workflow_charter=lighthouse_workflow_charter,
		decision_record=decision_record,
		review_window_start=window_start,
		review_window_end=window_end,
		policy_version=policy_version_text,
		context=context,
		items=sorted_items,
	)
	return sorted_items


def _build_item(
	*,
	decision: dict[str, Any],
	window_start: date,
	window_end: date,
	policy_version: str,
	context: Sprint4Feature4GovernanceContext,
) -> Sprint4Feature4GovernanceItem:
	evidence = context.evidence_package
	missing_fields, non_reviewable_fields = _collect_evidence_violations(evidence)
	defer_type_provided = DEFER_BLOCKER_TYPE_FIELD in evidence
	defer_ref_provided = DEFER_BLOCKER_REFERENCE_FIELD in evidence
	evidence_total = len(MANDATORY_EVIDENCE_FIELDS) + (1 if defer_type_provided else 0) + (1 if defer_ref_provided else 0)
	evidence_completeness_pct = round(
		(evidence_total - len(missing_fields) - len(non_reviewable_fields)) / evidence_total * 100,
		2,
	)
	rg_001 = 1 if not missing_fields and not non_reviewable_fields else 0

	rg_002, mutation_detected = _evaluate_additive_conformance(evidence, context.mutation_indicators)
	baseline_change_trigger_detected = 1 if mutation_detected == 1 else 0

	rg_003 = _evaluate_security_boundary(evidence)
	rg_004, explicit_rejection = _evaluate_approval_authority(evidence)
	rg_005 = _evaluate_release_governance_integrity(evidence.get("release_governance_record"))

	rg_006, rg_007, rg_008, rg_009, rg_010, rg_011 = _evaluate_operational_safety_criteria(
		evidence.get("operational_safety_record")
	)
	rg_012 = _evaluate_traceability_audit(evidence)

	gate_1_pass = rg_002
	gate_2_pass = rg_001
	gate_3_pass = _evaluate_gate_3_objective_conformance(evidence, rg_001)
	gate_4_pass = 1 if all(x == 1 for x in (rg_003, rg_004, rg_005, rg_012)) else 0
	gate_5_pass = 1 if all(x == 1 for x in (rg_006, rg_007, rg_008, rg_009, rg_010, rg_011)) else 0
	gate_sequence_passed = 1 if all(x == 1 for x in (gate_1_pass, gate_2_pass, gate_3_pass, gate_4_pass, gate_5_pass)) else 0

	mandatory_evidence_failed = 1 if rg_001 == 0 else 0
	mandatory_gate_failed = 1 if gate_sequence_passed == 0 else 0
	governance_approval_failed = 1 if rg_004 == 0 else 0
	critical_safety_failed = 1 if any(x == 0 for x in (rg_006, rg_007, rg_008, rg_009, rg_010, rg_011)) else 0
	baseline_or_contract_mutation_trigger = 1 if mutation_detected == 1 else 0

	defer_blocker_type = _normalize_status_text(evidence.get(DEFER_BLOCKER_TYPE_FIELD))
	defer_blocker_ref_reviewable = _has_reviewable_value(evidence.get(DEFER_BLOCKER_REFERENCE_FIELD))
	defer_blocker_type_present = _has_reviewable_value(evidence.get(DEFER_BLOCKER_TYPE_FIELD))
	defer_blocker_type_invalid = 1 if (defer_blocker_type_present and defer_blocker_type not in DEFER_BLOCKER_ALLOWED) else 0
	defer_missing_type = 1 if (defer_ref_provided and not defer_blocker_type_present) else 0
	defer_missing_reference = 1 if (defer_blocker_type_present and DEFER_BLOCKER_REFERENCE_FIELD not in evidence) else 0
	defer_non_reviewable_reference = 1 if (
		defer_blocker_type_present and DEFER_BLOCKER_REFERENCE_FIELD in evidence and not defer_blocker_ref_reviewable
	) else 0
	defer_allowed = 1 if (defer_blocker_type in DEFER_BLOCKER_ALLOWED and defer_blocker_ref_reviewable) else 0

	adr_route_required = 1 if baseline_or_contract_mutation_trigger == 1 else 0

	defer_condition_satisfied = 1 if (
		rg_001 == 1
		and gate_sequence_passed == 1
		and critical_safety_failed == 0
		and baseline_or_contract_mutation_trigger == 0
		and governance_approval_failed == 0
		and defer_allowed == 1
	) else 0
	go_condition_satisfied = 1 if (
		rg_001 == 1
		and gate_sequence_passed == 1
		and critical_safety_failed == 0
		and baseline_or_contract_mutation_trigger == 0
		and governance_approval_failed == 0
		and defer_blocker_type_present == 0
		and DEFER_BLOCKER_REFERENCE_FIELD not in evidence
	) else 0

	if baseline_or_contract_mutation_trigger == 1:
		outcome = NO_GO
	elif mandatory_evidence_failed == 1:
		outcome = NO_GO
	elif mandatory_gate_failed == 1:
		outcome = NO_GO
	elif governance_approval_failed == 1:
		outcome = NO_GO
	elif critical_safety_failed == 1:
		outcome = NO_GO
	elif defer_missing_type == 1:
		outcome = NO_GO
	elif defer_blocker_type_invalid == 1:
		outcome = NO_GO
	elif defer_missing_reference == 1:
		outcome = NO_GO
	elif defer_non_reviewable_reference == 1:
		outcome = NO_GO
	elif defer_condition_satisfied == 1:
		outcome = DEFER
	elif go_condition_satisfied == 1:
		outcome = GO
	else:
		outcome = NO_GO

	rationale = _build_rationale(
		missing_fields=missing_fields,
		non_reviewable_fields=non_reviewable_fields,
		mutation_detected=mutation_detected,
		explicit_rejection=explicit_rejection,
		critical_safety_failed=critical_safety_failed,
		defer_blocker_type=defer_blocker_type,
		defer_blocker_type_invalid=defer_blocker_type_invalid,
		defer_missing_type=defer_missing_type,
		defer_missing_reference=defer_missing_reference,
		defer_non_reviewable_reference=defer_non_reviewable_reference,
		outcome=outcome,
		governance_rationale=context.governance_rationale,
	)

	return Sprint4Feature4GovernanceItem(
		lighthouse_workflow_charter=decision.get("lighthouse_workflow_charter"),
		decision_record=decision.get("name"),
		review_window_start=window_start.isoformat(),
		review_window_end=window_end.isoformat(),
		policy_version=policy_version,
		readiness_outcome=outcome,
		implementation_authorized=0,
		adr_route_required=adr_route_required,
		baseline_change_trigger_detected=baseline_change_trigger_detected,
		evidence_completeness_pct=evidence_completeness_pct,
		rg_001_evidence_completeness_pass=rg_001,
		rg_002_additive_conformance_pass=rg_002,
		rg_003_security_boundary_pass=rg_003,
		rg_004_mandatory_approvals_pass=rg_004,
		rg_005_release_governance_integrity_pass=rg_005,
		rg_006_rollback_readiness_pass=rg_006,
		rg_007_incident_response_readiness_pass=rg_007,
		rg_008_recovery_readiness_pass=rg_008,
		rg_009_operational_verification_pass=rg_009,
		rg_010_monitoring_observability_pass=rg_010,
		rg_011_release_governance_readiness_pass=rg_011,
		rg_012_traceability_audit_pass=rg_012,
		gate_1_pass=gate_1_pass,
		gate_2_pass=gate_2_pass,
		gate_3_pass=gate_3_pass,
		gate_4_pass=gate_4_pass,
		gate_5_pass=gate_5_pass,
		gate_sequence_passed=gate_sequence_passed,
		governance_role_confirmed=1,
		read_only_confirmed=1,
		ranking_rationale=rationale,
	)


def _build_rationale(
	*,
	missing_fields: tuple[str, ...],
	non_reviewable_fields: tuple[str, ...],
	mutation_detected: int,
	explicit_rejection: int,
	critical_safety_failed: int,
	defer_blocker_type: str,
	defer_blocker_type_invalid: int,
	defer_missing_type: int,
	defer_missing_reference: int,
	defer_non_reviewable_reference: int,
	outcome: str,
	governance_rationale: str,
) -> str:
	parts: list[str] = []
	if missing_fields:
		parts.append(_("Mandatory evidence missing: {0}.").format(", ".join(missing_fields)))
	if non_reviewable_fields:
		parts.append(_("Mandatory evidence not reviewable: {0}.").format(", ".join(non_reviewable_fields)))
	if mutation_detected == 1:
		parts.append(_("Additive-only conformance failed: mutation intent detected; ADR route required."))
	if explicit_rejection == 1:
		parts.append(_("One or more mandatory governance approvals are explicitly rejected."))
	if critical_safety_failed == 1:
		parts.append(_("Mandatory operational safety or release-readiness criteria failed."))
	if defer_missing_type == 1:
		parts.append(_("DEFER validation failed: defer_blocker_type is missing."))
	if defer_blocker_type_invalid == 1:
		parts.append(_("DEFER validation failed: defer_blocker_type '{0}' is invalid.").format(defer_blocker_type))
	if defer_missing_reference == 1:
		parts.append(_("DEFER validation failed: defer_blocker_reference is missing."))
	if defer_non_reviewable_reference == 1:
		parts.append(_("DEFER validation failed: defer_blocker_reference is not reviewable."))
	if defer_blocker_type in DEFER_BLOCKER_ALLOWED:
		parts.append(_("DEFER blocker type: {0}.").format(defer_blocker_type))
	parts.append(_("Deterministic Sprint 4 Feature 4 governance outcome: {0}. Implementation authorization remains disabled.").format(outcome))
	if governance_rationale:
		parts.append(governance_rationale)
	return " ".join(parts)


def _collect_evidence_violations(evidence: dict[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
	missing: list[str] = []
	non_reviewable: list[str] = []
	for field_name in MANDATORY_EVIDENCE_FIELDS:
		if field_name not in evidence:
			missing.append(field_name)
			continue
		if not _has_reviewable_value(evidence.get(field_name)):
			non_reviewable.append(field_name)

	if DEFER_BLOCKER_TYPE_FIELD in evidence and not _has_reviewable_value(evidence.get(DEFER_BLOCKER_TYPE_FIELD)):
		non_reviewable.append(DEFER_BLOCKER_TYPE_FIELD)
	if DEFER_BLOCKER_REFERENCE_FIELD in evidence and not _has_reviewable_value(evidence.get(DEFER_BLOCKER_REFERENCE_FIELD)):
		non_reviewable.append(DEFER_BLOCKER_REFERENCE_FIELD)

	return tuple(sorted(set(missing))), tuple(sorted(set(non_reviewable)))


def _evaluate_additive_conformance(
	evidence: dict[str, Any], mutation_indicators: dict[str, int]
) -> tuple[int, int]:
	if any(cint(mutation_indicators.get(field) or 0) == 1 for field in MUTATION_INDICATOR_FIELDS):
		return 0, 1

	declaration_fields = (
		"additive_only_statement",
		"baseline_preservation_statement",
	)
	for field_name in declaration_fields:
		if _is_truthy_token(evidence.get(field_name)) != 1:
			return 0, 1

	if not _has_reviewable_value(evidence.get("contract_preservation_statement")):
		return 0, 1

	scope_decl = _normalize_status_text(evidence.get("scope_declaration"))
	if "sprint 4 feature 4" not in scope_decl:
		return 0, 1

	if _evaluate_contract_preservation_statement(evidence.get("contract_preservation_statement")) == 0:
		return 0, 1

	return 1, 0


def _evaluate_contract_preservation_statement(value: Any) -> int:
	text = _normalize_optional_text(value)
	if not text:
		return 0
	normalized = text.lower()
	required_markers = (
		"feature 1",
		"feature 2",
		"feature 3a",
		"feature 3b",
		"feature 4",
		"sprint 4 feature 1",
		"sprint 4 feature 2",
		"sprint 4 feature 3",
		"v0.2.0-baseline",
		"non-interference",
	)
	return 1 if all(marker in normalized for marker in required_markers) else 0


def _evaluate_gate_3_objective_conformance(evidence: dict[str, Any], rg_001: int) -> int:
	if rg_001 == 0:
		return 0
	if _has_reviewable_value(evidence.get("gate_assessment_record")) is False:
		return 0
	if _has_reviewable_value(evidence.get("validation_replay_record")) is False:
		return 0
	return 1


def _evaluate_security_boundary(evidence: dict[str, Any]) -> int:
	if _is_truthy_token(evidence.get("security_boundary_confirmation")) != 1:
		return 0
	if _has_reviewable_value(evidence.get("approval_authority_record")) is False:
		return 0
	return 1


def _evaluate_approval_authority(evidence: dict[str, Any]) -> tuple[int, int]:
	record = _normalize_optional_text(evidence.get("approval_authority_record"))
	if not record:
		return 0, 0

	normalized = record.lower()
	explicit_rejection = 1 if any(token in normalized for token in REJECTED_VALUE_SET) else 0
	for role in GOVERNANCE_ROLES:
		if role.lower() not in normalized:
			return 0, explicit_rejection

	if not any(token in normalized for token in APPROVED_VALUE_SET):
		return 0, explicit_rejection
	if explicit_rejection == 1:
		return 0, explicit_rejection
	return 1, explicit_rejection


def _evaluate_release_governance_integrity(value: Any) -> int:
	text = _normalize_optional_text(value)
	if not text:
		return 0
	normalized = text.lower()
	for role in GOVERNANCE_ROLES:
		if role.lower() not in normalized:
			return 0
	required_markers = ("release", "governance", "accountability", "approved")
	return 1 if all(marker in normalized for marker in required_markers) else 0


def _evaluate_operational_safety_criteria(value: Any) -> tuple[int, int, int, int, int, int]:
	if isinstance(value, dict):
		rollback = _is_truthy_token(value.get("rollback_readiness"))
		incident = _is_truthy_token(value.get("incident_response_readiness"))
		recovery = _is_truthy_token(value.get("recovery_readiness"))
		operational = _is_truthy_token(value.get("operational_verification_readiness"))
		monitoring = _is_truthy_token(value.get("monitoring_observability_readiness"))
		release_governance = _is_truthy_token(value.get("release_governance_readiness"))
		return rollback, incident, recovery, operational, monitoring, release_governance

	text = _normalize_optional_text(value)
	if not text:
		return 0, 0, 0, 0, 0, 0

	normalized = text.lower()
	if "not validated" in normalized:
		return 0, 0, 0, 0, 0, 0

	validated = "validated" in normalized or "confirmed" in normalized or "pass" in normalized
	rollback = 1 if validated and "rollback" in normalized else 0
	incident = 1 if validated and "incident" in normalized else 0
	recovery = 1 if validated and "recovery" in normalized else 0
	operational = 1 if validated and "operational verification" in normalized else 0
	monitoring = 1 if validated and ("monitoring" in normalized or "observability" in normalized) else 0
	release_governance = 1 if validated and "release governance" in normalized else 0
	return rollback, incident, recovery, operational, monitoring, release_governance


def _evaluate_traceability_audit(evidence: dict[str, Any]) -> int:
	if not _has_reviewable_value(evidence.get("traceability_audit_record")):
		return 0
	if not _has_reviewable_value(evidence.get("validation_replay_record")):
		return 0
	return 1


def _resolve_governance_context(value: dict[str, Any] | None) -> Sprint4Feature4GovernanceContext:
	payload = dict(value or {})
	evidence = payload.get("evidence_package")
	if evidence is None:
		evidence_fields = set(MANDATORY_EVIDENCE_FIELDS) | {DEFER_BLOCKER_TYPE_FIELD, DEFER_BLOCKER_REFERENCE_FIELD}
		evidence = {field: payload.get(field) for field in evidence_fields if field in payload}
	if evidence and not isinstance(evidence, dict):
		frappe.throw(_("evidence_package must be a JSON object."), exc=frappe.ValidationError)

	mutation_input = payload.get("mutation_indicators") or {}
	if mutation_input and not isinstance(mutation_input, dict):
		frappe.throw(_("mutation_indicators must be a JSON object."), exc=frappe.ValidationError)
	mutation_indicators = {
		field: cint((mutation_input or {}).get(field) or 0)
		for field in MUTATION_INDICATOR_FIELDS
	}
	if cint(payload.get("mutation_implied") or 0) == 1:
		mutation_indicators["mutates_approved_feature_contracts"] = 1

	return Sprint4Feature4GovernanceContext(
		evidence_package=dict(evidence or {}),
		mutation_indicators=mutation_indicators,
		governance_rationale=str(payload.get("governance_rationale") or "").strip(),
	)


def _validate_review_window(review_window_start: str, review_window_end: str) -> tuple[date, date]:
	start_text = _normalize_required_text(review_window_start, "Review Window Start")
	end_text = _normalize_required_text(review_window_end, "Review Window End")
	start = getdate(start_text)
	end = getdate(end_text)
	if start > end:
		frappe.throw(_("Review Window Start cannot be after Review Window End."), exc=frappe.ValidationError)
	return start, end


def _normalize_required_text(value: Any, field_label: str) -> str:
	text = _normalize_optional_text(value)
	if not text:
		frappe.throw(_("{0} is required.").format(field_label), exc=frappe.ValidationError)
	return text


def _normalize_optional_text(value: Any) -> str:
	if value is None:
		return ""
	return str(value).strip()


def _normalize_status_text(value: Any) -> str:
	return _normalize_optional_text(value).lower()


def _has_reviewable_value(value: Any) -> bool:
	if value is None:
		return False
	if isinstance(value, str):
		return bool(value.strip())
	if isinstance(value, (list, tuple, set, dict)):
		return bool(value)
	return True


def _is_truthy_token(value: Any) -> int:
	text = _normalize_status_text(value)
	return 1 if text in TRUTHY_VALUE_SET else 0


def _fetch_decision_docs(lighthouse_workflow_charter: str, decision_record: str | None) -> tuple[dict[str, Any], ...]:
	filters = {"lighthouse_workflow_charter": lighthouse_workflow_charter}
	if decision_record:
		filters["name"] = decision_record

	rows = frappe.get_list(
		"Decision Record",
		filters=filters,
		fields=["name", "lighthouse_workflow_charter", "approval_state", "accountable_owner", "executive_sponsor"],
	)
	if decision_record and not rows:
		frappe.throw(_("Decision Record {0} was not found for the selected charter.").format(decision_record))
	return tuple(rows)


def _item_sort_key(item: Sprint4Feature4GovernanceItem) -> tuple[Any, ...]:
	return (item.decision_record, item.readiness_outcome)


def _record_actor_trace_audit_evidence(
	*,
	invocation_context: str,
	lighthouse_workflow_charter: str,
	decision_record: str | None,
	review_window_start: date,
	review_window_end: date,
	policy_version: str,
	context: Sprint4Feature4GovernanceContext,
	items: tuple[Sprint4Feature4GovernanceItem, ...],
) -> None:
	payload = {
		"event": "sprint4_feature4_verification_auditability_release_governance_review_executed",
		"actor": frappe.session.user,
		"executed_at": now_datetime().isoformat(),
		"report_invocation_context": invocation_context,
		"governance_review_context": {
			"policy_version": policy_version,
		},
		"requested_review_window": {
			"start": review_window_start.isoformat(),
			"end": review_window_end.isoformat(),
		},
		"source_charter": lighthouse_workflow_charter,
		"decision_record": decision_record or "",
		"result_count": len(items),
		"evidence_fields_count": len(context.evidence_package),
	}
	frappe.logger(S4F4_AUDIT_LOGGER_NAME).info(payload)


def _require_governance_role() -> None:
	roles = set(frappe.get_roles())
	if not roles.intersection(GOVERNANCE_ROLES):
		frappe.throw(
			_("Sprint 4 Feature 4 governance review requires a governance role."),
			exc=frappe.PermissionError,
		)


def _require_read_permissions() -> None:
	for doctype in (
		"Lighthouse Workflow Charter",
		"Decision Record",
		"Dependency Exception Record",
		"Attribution Case",
	):
		frappe.has_permission(doctype, ptype="read", throw=True)


__all__ = [
	"DEFER",
	"GO",
	"NO_GO",
	"Sprint4Feature4GovernanceContext",
	"Sprint4Feature4GovernanceItem",
	"evaluate_sprint4_feature4_verification_auditability_release_governance",
]
