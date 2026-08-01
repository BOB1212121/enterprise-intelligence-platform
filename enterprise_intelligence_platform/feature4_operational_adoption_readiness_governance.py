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

FEATURE4_REPORT_NAME = "Feature 4 Operational Adoption Readiness Governance Review"
FEATURE4_REPORT_MODULE = "Enterprise Intelligence Platform"
FEATURE4_REPORT_REF_DOCTYPE = "Decision Record"
FEATURE4_AUDIT_LOGGER_NAME = "enterprise_intelligence_platform.feature4"

PROHIBITED_DUPLICATE_PERSISTENCE_DOCTYPES = (
	"Follow Through Item",
	"Follow Through Cycle",
	"Escalation Case",
	"FollowThroughItem",
	"FollowThroughCycle",
	"EscalationCase",
)

GO = "GO"
DEFER = "DEFER"
NO_GO = "NO-GO"

MANDATORY_EVIDENCE_FIELDS = (
	"readiness_package_id",
	"policy_version",
	"target_readiness_window_start",
	"target_readiness_window_end",
	"feature_scope_declaration",
	"additive_only_conformance_declaration",
	"baseline_contract_preservation_declaration",
	"feature_1_contract_preservation_declaration",
	"feature_2_contract_preservation_declaration",
	"feature_3a_contract_preservation_declaration",
	"feature_3b_contract_preservation_declaration",
	"baseline_change_trigger_status",
	"adr_route_status",
	"rollback_readiness_reference",
	"incident_response_readiness_reference",
	"regression_coverage_declaration",
	"security_access_control_declaration",
	"traceability_evidence_references",
	"approver_decision_workflow_owner",
	"approver_decision_executive_sponsor",
	"approver_decision_system_manager",
	"approver_decision_operations_manager",
	"decision_timestamp",
	"decision_actor",
	"proposed_readiness_outcome",
)

MUTATION_INDICATOR_FIELDS = (
	"modifies_workflow_semantics",
	"changes_approval_state_semantics",
	"changes_permission_authority",
	"changes_ownership_or_source_of_truth",
	"changes_immutability_behavior",
	"changes_baseline_authoritative_persistence",
	"mutates_approved_feature_contracts",
)

APPROVED_VALUE_FIELD_MAP = {
	"EIP Workflow Owner": "approver_decision_workflow_owner",
	"EIP Executive Sponsor": "approver_decision_executive_sponsor",
	"System Manager": "approver_decision_system_manager",
	"EIP Operations Manager": "approver_decision_operations_manager",
}

APPROVED_VALUE_SET = {"approved", "yes", "true", "1"}
REJECTED_VALUE_SET = {"rejected", "no", "false", "0"}
TRUTHY_VALUE_SET = {"approved", "yes", "true", "1", "confirmed", "pass", "validated"}

TRIGGER_STATUS_NOT_TRIGGERED = {"not_triggered", "none", "no_trigger", "no"}
TRIGGER_STATUS_ROUTED = {"triggered_routed", "routed", "triggered_adr_routed"}
TRIGGER_STATUS_UNRESOLVED = {"triggered_unresolved", "unresolved", "triggered", "yes", "open"}
ADR_ROUTE_STATUS_ROUTED = {"required_routed", "routed", "adr_routed"}


@dataclass(frozen=True)
class Feature4ReadinessContext:
	evidence_package: dict[str, Any]
	mutation_indicators: dict[str, int]
	governance_rationale: str


@dataclass(frozen=True)
class Feature4ReadinessGovernanceItem:
	lighthouse_workflow_charter: str
	decision_record: str
	review_window_start: str
	review_window_end: str
	policy_version: str
	readiness_outcome: str
	implementation_authorized: int
	adr_route_required: int
	baseline_change_trigger_detected: int
	baseline_change_trigger_status: str
	evidence_completeness_pct: float
	rg_001_evidence_completeness_pass: int
	rg_002_additive_conformance_pass: int
	rg_003_baseline_trigger_status_pass: int
	rg_004_mandatory_approvals_pass: int
	rg_005_rollback_readiness_pass: int
	rg_006_incident_response_readiness_pass: int
	rg_007_regression_coverage_pass: int
	rg_008_traceability_audit_pass: int
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
			"baseline_change_trigger_status": self.baseline_change_trigger_status,
			"evidence_completeness_pct": self.evidence_completeness_pct,
			"rg_001_evidence_completeness_pass": self.rg_001_evidence_completeness_pass,
			"rg_002_additive_conformance_pass": self.rg_002_additive_conformance_pass,
			"rg_003_baseline_trigger_status_pass": self.rg_003_baseline_trigger_status_pass,
			"rg_004_mandatory_approvals_pass": self.rg_004_mandatory_approvals_pass,
			"rg_005_rollback_readiness_pass": self.rg_005_rollback_readiness_pass,
			"rg_006_incident_response_readiness_pass": self.rg_006_incident_response_readiness_pass,
			"rg_007_regression_coverage_pass": self.rg_007_regression_coverage_pass,
			"rg_008_traceability_audit_pass": self.rg_008_traceability_audit_pass,
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


def evaluate_feature4_readiness_governance(
	*,
	lighthouse_workflow_charter: str,
	review_window_start: str,
	review_window_end: str,
	policy_version: str,
	decision_record: str | None = None,
	readiness_context: dict[str, Any] | None = None,
	invocation_context: str = "direct_helper_call",
) -> tuple[Feature4ReadinessGovernanceItem, ...]:
	_require_governance_role()
	_require_read_permissions()
	_enforce_no_unresolved_runtime_guard_risks()

	window_start, window_end = _validate_review_window(review_window_start, review_window_end)
	policy_version_text = _normalize_required_text(policy_version, "Policy Version")
	context = _resolve_readiness_context(readiness_context)

	decision_rows = _fetch_decision_docs(lighthouse_workflow_charter, decision_record)
	items: list[Feature4ReadinessGovernanceItem] = []
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
	context: Feature4ReadinessContext,
) -> Feature4ReadinessGovernanceItem:
	evidence = context.evidence_package
	missing_fields, non_reviewable_fields = _collect_evidence_violations(evidence)
	evidence_completeness_pct = round(
		(len(MANDATORY_EVIDENCE_FIELDS) - len(missing_fields) - len(non_reviewable_fields))
		/ len(MANDATORY_EVIDENCE_FIELDS)
		* 100,
		2,
	)
	rg_001 = 1 if not missing_fields and not non_reviewable_fields else 0

	mutation_detected = _detect_mutation_intent(evidence=evidence, mutation_indicators=context.mutation_indicators)
	rg_002 = 0 if mutation_detected else 1

	trigger_status = _normalize_status_text(evidence.get("baseline_change_trigger_status"))
	adr_route_status = _normalize_status_text(evidence.get("adr_route_status"))
	trigger_detected = 1 if trigger_status in (TRIGGER_STATUS_UNRESOLVED | TRIGGER_STATUS_ROUTED) else 0
	trigger_unresolved = 1 if trigger_status in TRIGGER_STATUS_UNRESOLVED else 0
	trigger_routed = 1 if trigger_status in TRIGGER_STATUS_ROUTED and adr_route_status in ADR_ROUTE_STATUS_ROUTED else 0
	rg_003 = 1 if trigger_unresolved == 0 else 0

	approvals_complete, explicit_rejection = _evaluate_approvals(evidence)
	rg_004 = approvals_complete

	rg_005 = _evaluate_operational_readiness_field(
		value=evidence.get("rollback_readiness_reference"),
		window_start=evidence.get("target_readiness_window_start"),
		window_end=evidence.get("target_readiness_window_end"),
	)
	rg_006 = _evaluate_operational_readiness_field(
		value=evidence.get("incident_response_readiness_reference"),
		window_start=evidence.get("target_readiness_window_start"),
		window_end=evidence.get("target_readiness_window_end"),
	)
	rg_007 = _evaluate_regression_coverage(evidence.get("regression_coverage_declaration"))
	rg_008 = _evaluate_traceability_audit(evidence)

	gate_1_pass = rg_001
	gate_2_pass = rg_002
	gate_3_pass = 1 if (trigger_unresolved == 0 or trigger_routed == 1) else 0
	gate_4_pass = 1 if all(x == 1 for x in (rg_005, rg_006, rg_007)) else 0
	gate_5_pass = 1 if all(x == 1 for x in (gate_1_pass, gate_2_pass, gate_3_pass, gate_4_pass, rg_004, rg_008)) else 0
	gate_sequence_passed = 1 if all(x == 1 for x in (gate_1_pass, gate_2_pass, gate_3_pass, gate_4_pass, gate_5_pass)) else 0

	critical_safety_failed = 1 if (rg_005 == 0 or rg_006 == 0) else 0
	mandatory_evidence_failed = 1 if rg_001 == 0 else 0
	approvals_failed = 1 if rg_004 == 0 else 0
	unresolved_trigger_without_route = 1 if trigger_unresolved == 1 and trigger_routed == 0 else 0
	adr_route_required = 1 if (mutation_detected or trigger_detected) else 0

	if mutation_detected:
		outcome = NO_GO
	elif mandatory_evidence_failed == 1:
		outcome = NO_GO
	elif approvals_failed == 1:
		outcome = NO_GO
	elif critical_safety_failed == 1:
		outcome = NO_GO
	elif unresolved_trigger_without_route == 1:
		outcome = NO_GO
	elif trigger_routed == 1:
		outcome = DEFER
	elif gate_sequence_passed == 1:
		outcome = GO
	else:
		outcome = DEFER

	implementation_authorized = 0

	rationale = _build_rationale(
		missing_fields=missing_fields,
		non_reviewable_fields=non_reviewable_fields,
		mutation_detected=mutation_detected,
		trigger_status=trigger_status,
		adr_route_status=adr_route_status,
		explicit_rejection=explicit_rejection,
		critical_safety_failed=critical_safety_failed,
		outcome=outcome,
		governance_rationale=context.governance_rationale,
	)

	return Feature4ReadinessGovernanceItem(
		lighthouse_workflow_charter=decision.get("lighthouse_workflow_charter"),
		decision_record=decision.get("name"),
		review_window_start=window_start.isoformat(),
		review_window_end=window_end.isoformat(),
		policy_version=policy_version,
		readiness_outcome=outcome,
		implementation_authorized=implementation_authorized,
		adr_route_required=adr_route_required,
		baseline_change_trigger_detected=trigger_detected,
		baseline_change_trigger_status=trigger_status or "not_provided",
		evidence_completeness_pct=evidence_completeness_pct,
		rg_001_evidence_completeness_pass=rg_001,
		rg_002_additive_conformance_pass=rg_002,
		rg_003_baseline_trigger_status_pass=rg_003,
		rg_004_mandatory_approvals_pass=rg_004,
		rg_005_rollback_readiness_pass=rg_005,
		rg_006_incident_response_readiness_pass=rg_006,
		rg_007_regression_coverage_pass=rg_007,
		rg_008_traceability_audit_pass=rg_008,
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
	trigger_status: str,
	adr_route_status: str,
	explicit_rejection: int,
	critical_safety_failed: int,
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
	if trigger_status:
		parts.append(_("Baseline change trigger status: {0}; ADR route status: {1}.").format(trigger_status, adr_route_status or "not_provided"))
	if explicit_rejection == 1:
		parts.append(_("One or more mandatory approver decisions are explicitly rejected."))
	if critical_safety_failed == 1:
		parts.append(_("Critical safety controls failed: rollback-readiness and/or incident-response readiness."))
	parts.append(_("Deterministic readiness outcome: {0}. Implementation authorization remains disabled in Feature 4 planning-only stage.").format(outcome))
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
	return tuple(sorted(missing)), tuple(sorted(non_reviewable))


def _detect_mutation_intent(*, evidence: dict[str, Any], mutation_indicators: dict[str, int]) -> int:
	if any(cint(mutation_indicators.get(field) or 0) == 1 for field in MUTATION_INDICATOR_FIELDS):
		return 1

	declaration_fields = (
		"additive_only_conformance_declaration",
		"baseline_contract_preservation_declaration",
		"feature_1_contract_preservation_declaration",
		"feature_2_contract_preservation_declaration",
		"feature_3a_contract_preservation_declaration",
		"feature_3b_contract_preservation_declaration",
	)
	for field_name in declaration_fields:
		if _is_truthy_token(evidence.get(field_name)) != 1:
			return 1
	return 0


def _evaluate_approvals(evidence: dict[str, Any]) -> tuple[int, int]:
	explicit_rejection = 0
	for role, field_name in APPROVED_VALUE_FIELD_MAP.items():
		_ = role
		value = _normalize_status_text(evidence.get(field_name))
		if value in REJECTED_VALUE_SET:
			explicit_rejection = 1
		if value not in APPROVED_VALUE_SET:
			return 0, explicit_rejection
	return 1, explicit_rejection


def _evaluate_operational_readiness_field(*, value: Any, window_start: Any, window_end: Any) -> int:
	if isinstance(value, dict):
		validated = _is_truthy_token(value.get("validated"))
		if validated != 1:
			return 0
		if _normalize_optional_text(window_start) and _normalize_optional_text(window_end):
			if _normalize_optional_text(value.get("window_start")) != _normalize_optional_text(window_start):
				return 0
			if _normalize_optional_text(value.get("window_end")) != _normalize_optional_text(window_end):
				return 0
		return 1

	text = _normalize_optional_text(value)
	if not text:
		return 0
	normalized = text.lower()
	if "not validated" in normalized:
		return 0
	return 1 if "validated" in normalized else 0


def _evaluate_regression_coverage(value: Any) -> int:
	text = _normalize_optional_text(value)
	if not text:
		return 0
	normalized = text.lower()
	required_markers = (
		"baseline",
		"feature 1",
		"feature 2",
		"feature 3a",
		"feature 3b",
		"non-interference",
	)
	return 1 if all(marker in normalized for marker in required_markers) else 0


def _evaluate_traceability_audit(evidence: dict[str, Any]) -> int:
	if not _has_reviewable_value(evidence.get("decision_actor")):
		return 0
	if not _has_reviewable_value(evidence.get("decision_timestamp")):
		return 0
	if not _has_reviewable_value(evidence.get("policy_version")):
		return 0
	if not _has_reviewable_value(evidence.get("traceability_evidence_references")):
		return 0
	outcome = _normalize_status_text(evidence.get("proposed_readiness_outcome"))
	if outcome not in {"go", "defer", "no-go"}:
		return 0
	return 1


def _resolve_readiness_context(value: dict[str, Any] | None) -> Feature4ReadinessContext:
	payload = dict(value or {})
	evidence = payload.get("evidence_package")
	if evidence is None:
		evidence = {field: payload.get(field) for field in MANDATORY_EVIDENCE_FIELDS if field in payload}
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

	return Feature4ReadinessContext(
		evidence_package=dict(evidence or {}),
		mutation_indicators=mutation_indicators,
		governance_rationale=str(payload.get("governance_rationale") or "").strip(),
	)


def _enforce_no_unresolved_runtime_guard_risks() -> None:
	risk_map = _evaluate_runtime_guard_risks()
	unresolved = tuple(sorted(code for code, active in risk_map.items() if active))
	if unresolved:
		frappe.throw(
			_("Feature 4 blocked due to unresolved baseline/runtime guard risks: {0}.").format(", ".join(unresolved)),
			exc=frappe.ValidationError,
		)


def _evaluate_runtime_guard_risks() -> dict[str, bool]:
	return {
		"duplicate_source_of_truth_persistence_risk": _detect_duplicate_source_of_truth_persistence_risk(),
		"ownership_mapping_mutation_risk": _detect_ownership_mapping_mutation_risk(),
		"runtime_contract_mutation_risk": _detect_runtime_contract_mutation_risk(),
	}


def _detect_duplicate_source_of_truth_persistence_risk() -> bool:
	for doctype_name in PROHIBITED_DUPLICATE_PERSISTENCE_DOCTYPES:
		if frappe.db.exists("DocType", doctype_name):
			return True
	return False


def _detect_ownership_mapping_mutation_risk() -> bool:
	if not frappe.db.exists("Report", FEATURE4_REPORT_NAME):
		return True

	report_roles = set(
		frappe.get_all(
			"Has Role",
			filters={"parent": FEATURE4_REPORT_NAME, "parenttype": "Report", "parentfield": "roles"},
			pluck="role",
		)
	)
	return report_roles != set(GOVERNANCE_ROLES)


def _detect_runtime_contract_mutation_risk() -> bool:
	report_row = frappe.db.get_value(
		"Report",
		FEATURE4_REPORT_NAME,
		["report_type", "is_standard", "module", "ref_doctype"],
		as_dict=True,
	)
	if not report_row:
		return True
	if report_row.report_type != "Script Report":
		return True
	if report_row.is_standard != "Yes":
		return True
	if report_row.module != FEATURE4_REPORT_MODULE:
		return True
	if report_row.ref_doctype != FEATURE4_REPORT_REF_DOCTYPE:
		return True
	return False


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


def _item_sort_key(item: Feature4ReadinessGovernanceItem) -> tuple[Any, ...]:
	return (
		item.decision_record,
		item.readiness_outcome,
	)


def _record_actor_trace_audit_evidence(
	*,
	invocation_context: str,
	lighthouse_workflow_charter: str,
	decision_record: str | None,
	review_window_start: date,
	review_window_end: date,
	policy_version: str,
	context: Feature4ReadinessContext,
	items: tuple[Feature4ReadinessGovernanceItem, ...],
) -> None:
	payload = {
		"event": "feature4_readiness_governance_review_executed",
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
	frappe.logger(FEATURE4_AUDIT_LOGGER_NAME).info(payload)


def _require_governance_role() -> None:
	roles = set(frappe.get_roles())
	if not roles.intersection(GOVERNANCE_ROLES):
		frappe.throw(
			_("Feature 4 Operational Adoption Readiness Governance Review requires a governance role."),
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
	"Feature4ReadinessContext",
	"Feature4ReadinessGovernanceItem",
	"evaluate_feature4_readiness_governance",
]
