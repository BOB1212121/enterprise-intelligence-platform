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

FEATURE3B_REPORT_NAME = "Feature 3B Baseline Change Governance Review"
FEATURE3B_REPORT_MODULE = "Enterprise Intelligence Platform"
FEATURE3B_REPORT_REF_DOCTYPE = "Decision Record"
FEATURE3B_AUDIT_LOGGER_NAME = "enterprise_intelligence_platform.feature3b"

PROHIBITED_DUPLICATE_PERSISTENCE_DOCTYPES = (
	"Follow Through Item",
	"Follow Through Cycle",
	"Escalation Case",
	"FollowThroughItem",
	"FollowThroughCycle",
	"EscalationCase",
)

TRIGGER_RULE_FIELDS = (
	"modifies_workflow_semantics",
	"modifies_permission_semantics",
	"alters_ownership_or_source_of_truth",
	"changes_immutability_behavior",
	"changes_approval_state_semantics",
	"introduces_conflicting_duplicate_source_of_truth_persistence",
	"mutates_approved_feature_contracts",
)

REQUESTED_DISPOSITION_CONTINUE_BLOCKED = "continue_blocked"
REQUESTED_DISPOSITION_REJECT = "reject_baseline_change"
REQUESTED_DISPOSITION_ACCEPT_FUTURE_TRACK = "accept_future_baseline_change_path"
ALLOWED_REQUESTED_DISPOSITIONS = {
	REQUESTED_DISPOSITION_CONTINUE_BLOCKED,
	REQUESTED_DISPOSITION_REJECT,
	REQUESTED_DISPOSITION_ACCEPT_FUTURE_TRACK,
}

OUTCOME_NOT_TRIGGERED = "Not triggered"
OUTCOME_CONTINUE_BLOCKED = "Continue blocked"
OUTCOME_REJECTED = "Rejected"
OUTCOME_APPROVED_FUTURE_TRACK = "Approved for future baseline-change track"

MANDATORY_DISPOSITION_APPROVER_ROLES = (
	"EIP Workflow Owner",
	"EIP Executive Sponsor",
	"System Manager",
)
REENTRY_REQUIRED_ROLE = "EIP Operations Manager"

MANDATORY_ADR_EVIDENCE_FIELDS = (
	"trigger_identifiers",
	"trigger_description",
	"triggering_feature_and_capability",
	"affected_baseline_artifacts",
	"impact_assessment",
	"alternatives_considered",
	"baseline_change_justification",
	"risk_assessment",
	"architecture_impact_assessment",
	"baseline_compatibility_assessment",
	"traceability_references",
	"requested_disposition",
	"decision_owners",
)

MANDATORY_STOP_DECLARATION_FIELDS = (
	"trigger_identifier",
	"trigger_timestamp",
	"triggered_feature",
	"implementation_stop_reason",
	"affected_scope",
	"responsible_governance_owner",
	"adr_reference",
	"current_disposition",
	"reentry_conditions",
)


@dataclass(frozen=True)
class Feature3BBaselineChangeContext:
	trigger_flags: dict[str, int]
	requested_disposition: str
	adr_evidence: dict[str, Any]
	approver_decisions: dict[str, int]
	architecture_approval_granted: int
	scope_mixed_with_additive: int
	stop_declaration: dict[str, Any]
	governance_rationale: str


@dataclass(frozen=True)
class Feature3BBaselineChangeGovernanceItem:
	lighthouse_workflow_charter: str
	decision_record: str
	review_window_start: str
	review_window_end: str
	policy_version: str
	baseline_change_trigger_detected: int
	baseline_change_trigger_codes: str
	implementation_stop_required: int
	adr_route_required: int
	adr_initiation_blocked: int
	adr_evidence_complete: int
	mandatory_disposition_approvals_complete: int
	architecture_approval_granted: int
	implementation_stop_declaration_complete: int
	implementation_stop_declaration_resolved: int
	disposition_outcome: str
	reentry_planning_authorized: int
	implementation_authorized: int
	scope_isolation_confirmed: int
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
			"baseline_change_trigger_detected": self.baseline_change_trigger_detected,
			"baseline_change_trigger_codes": self.baseline_change_trigger_codes,
			"implementation_stop_required": self.implementation_stop_required,
			"adr_route_required": self.adr_route_required,
			"adr_initiation_blocked": self.adr_initiation_blocked,
			"adr_evidence_complete": self.adr_evidence_complete,
			"mandatory_disposition_approvals_complete": self.mandatory_disposition_approvals_complete,
			"architecture_approval_granted": self.architecture_approval_granted,
			"implementation_stop_declaration_complete": self.implementation_stop_declaration_complete,
			"implementation_stop_declaration_resolved": self.implementation_stop_declaration_resolved,
			"disposition_outcome": self.disposition_outcome,
			"reentry_planning_authorized": self.reentry_planning_authorized,
			"implementation_authorized": self.implementation_authorized,
			"scope_isolation_confirmed": self.scope_isolation_confirmed,
			"governance_role_confirmed": self.governance_role_confirmed,
			"read_only_confirmed": self.read_only_confirmed,
			"ranking_rationale": self.ranking_rationale,
		}


def evaluate_feature3b_baseline_change_governance(
	*,
	lighthouse_workflow_charter: str,
	review_window_start: str,
	review_window_end: str,
	policy_version: str,
	decision_record: str | None = None,
	baseline_change_context: dict[str, Any] | None = None,
	invocation_context: str = "direct_helper_call",
) -> tuple[Feature3BBaselineChangeGovernanceItem, ...]:
	_require_governance_role()
	_require_read_permissions()
	_enforce_no_unresolved_runtime_guard_risks()

	window_start, window_end = _validate_review_window(review_window_start, review_window_end)
	policy_version_text = _normalize_required_text(policy_version, "Policy Version")
	context = _resolve_baseline_change_context(baseline_change_context)

	decision_rows = _fetch_decision_docs(lighthouse_workflow_charter, decision_record)
	items: list[Feature3BBaselineChangeGovernanceItem] = []
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
	context: Feature3BBaselineChangeContext,
) -> Feature3BBaselineChangeGovernanceItem:
	trigger_codes = tuple(sorted(code for code, active in context.trigger_flags.items() if cint(active) == 1))
	trigger_detected = 1 if trigger_codes else 0
	implementation_stop_required = trigger_detected
	adr_route_required = trigger_detected

	adr_evidence_complete = _is_adr_evidence_complete(context.adr_evidence)
	adr_initiation_blocked = 1 if trigger_detected and adr_evidence_complete != 1 else 0
	disposition_approvals_complete = _has_all_approved(
		context.approver_decisions,
		roles=MANDATORY_DISPOSITION_APPROVER_ROLES,
	)
	architecture_approval_granted = cint(context.architecture_approval_granted)
	scope_isolation_confirmed = 0 if cint(context.scope_mixed_with_additive) == 1 else 1
	stop_declaration_complete = _is_stop_declaration_complete(context.stop_declaration)

	preliminary_outcome = _determine_preliminary_disposition_outcome(
		trigger_detected=trigger_detected,
		adr_evidence_complete=adr_evidence_complete,
		disposition_approvals_complete=disposition_approvals_complete,
		architecture_approval_granted=architecture_approval_granted,
		scope_isolation_confirmed=scope_isolation_confirmed,
		requested_disposition=context.requested_disposition,
	)

	stop_declaration_resolved = _is_stop_declaration_resolved(
		stop_declaration=context.stop_declaration,
		stop_declaration_complete=stop_declaration_complete,
		outcome=preliminary_outcome,
	)

	final_outcome = preliminary_outcome
	if trigger_detected and (stop_declaration_complete != 1 or stop_declaration_resolved != 1):
		final_outcome = OUTCOME_CONTINUE_BLOCKED

	reentry_approvals_complete = _has_all_approved(
		context.approver_decisions,
		roles=(*MANDATORY_DISPOSITION_APPROVER_ROLES, REENTRY_REQUIRED_ROLE),
	)
	reentry_planning_authorized = 1 if (
		final_outcome == OUTCOME_APPROVED_FUTURE_TRACK and reentry_approvals_complete == 1
	) else 0

	implementation_authorized = 0

	rationale = _build_rationale(
		context=context,
		trigger_detected=trigger_detected,
		trigger_codes=trigger_codes,
		adr_evidence_complete=adr_evidence_complete,
		disposition_approvals_complete=disposition_approvals_complete,
		architecture_approval_granted=architecture_approval_granted,
		stop_declaration_complete=stop_declaration_complete,
		stop_declaration_resolved=stop_declaration_resolved,
		scope_isolation_confirmed=scope_isolation_confirmed,
		final_outcome=final_outcome,
	)

	return Feature3BBaselineChangeGovernanceItem(
		lighthouse_workflow_charter=decision.get("lighthouse_workflow_charter"),
		decision_record=decision.get("name"),
		review_window_start=window_start.isoformat(),
		review_window_end=window_end.isoformat(),
		policy_version=policy_version,
		baseline_change_trigger_detected=trigger_detected,
		baseline_change_trigger_codes=", ".join(trigger_codes) if trigger_codes else "—",
		implementation_stop_required=implementation_stop_required,
		adr_route_required=adr_route_required,
		adr_initiation_blocked=adr_initiation_blocked,
		adr_evidence_complete=adr_evidence_complete,
		mandatory_disposition_approvals_complete=disposition_approvals_complete,
		architecture_approval_granted=architecture_approval_granted,
		implementation_stop_declaration_complete=stop_declaration_complete,
		implementation_stop_declaration_resolved=stop_declaration_resolved,
		disposition_outcome=final_outcome,
		reentry_planning_authorized=reentry_planning_authorized,
		implementation_authorized=implementation_authorized,
		scope_isolation_confirmed=scope_isolation_confirmed,
		governance_role_confirmed=1,
		read_only_confirmed=1,
		ranking_rationale=rationale,
	)


def _determine_preliminary_disposition_outcome(
	*,
	trigger_detected: int,
	adr_evidence_complete: int,
	disposition_approvals_complete: int,
	architecture_approval_granted: int,
	scope_isolation_confirmed: int,
	requested_disposition: str,
) -> str:
	if trigger_detected != 1:
		return OUTCOME_NOT_TRIGGERED
	if scope_isolation_confirmed != 1:
		return OUTCOME_CONTINUE_BLOCKED
	if adr_evidence_complete != 1:
		return OUTCOME_CONTINUE_BLOCKED
	if disposition_approvals_complete != 1:
		return OUTCOME_CONTINUE_BLOCKED
	if architecture_approval_granted != 1:
		return OUTCOME_CONTINUE_BLOCKED
	if requested_disposition == REQUESTED_DISPOSITION_REJECT:
		return OUTCOME_REJECTED
	if requested_disposition == REQUESTED_DISPOSITION_ACCEPT_FUTURE_TRACK:
		return OUTCOME_APPROVED_FUTURE_TRACK
	return OUTCOME_CONTINUE_BLOCKED


def _is_adr_evidence_complete(adr_evidence: dict[str, Any]) -> int:
	for field_name in MANDATORY_ADR_EVIDENCE_FIELDS:
		if not _has_reviewable_value(adr_evidence.get(field_name)):
			return 0
	return 1


def _is_stop_declaration_complete(stop_declaration: dict[str, Any]) -> int:
	for field_name in MANDATORY_STOP_DECLARATION_FIELDS:
		if not _has_reviewable_value(stop_declaration.get(field_name)):
			return 0
	return 1


def _is_stop_declaration_resolved(
	*,
	stop_declaration: dict[str, Any],
	stop_declaration_complete: int,
	outcome: str,
) -> int:
	if stop_declaration_complete != 1:
		return 0
	if outcome in {OUTCOME_NOT_TRIGGERED, OUTCOME_CONTINUE_BLOCKED}:
		return 0
	current_disposition = str(stop_declaration.get("current_disposition") or "").strip().lower()
	if outcome == OUTCOME_REJECTED:
		return 1 if current_disposition == "rejected" else 0
	if outcome == OUTCOME_APPROVED_FUTURE_TRACK:
		return 1 if current_disposition == "approved for future baseline-change track" else 0
	return 0


def _has_all_approved(approver_decisions: dict[str, int], *, roles: tuple[str, ...]) -> int:
	for role in roles:
		if cint(approver_decisions.get(role) or 0) != 1:
			return 0
	return 1


def _build_rationale(
	*,
	context: Feature3BBaselineChangeContext,
	trigger_detected: int,
	trigger_codes: tuple[str, ...],
	adr_evidence_complete: int,
	disposition_approvals_complete: int,
	architecture_approval_granted: int,
	stop_declaration_complete: int,
	stop_declaration_resolved: int,
	scope_isolation_confirmed: int,
	final_outcome: str,
) -> str:
	parts: list[str] = []
	if trigger_detected == 1:
		parts.append(_("Baseline Change trigger detected ({0}); mandatory stop and ADR routing enforced.").format(", ".join(trigger_codes)))
	else:
		parts.append(_("No Baseline Change trigger detected for the supplied evidence context."))

	if adr_evidence_complete != 1:
		parts.append(_("ADR initiation evidence package is incomplete; ADR initiation remains blocked."))
	if disposition_approvals_complete != 1:
		parts.append(_("Mandatory disposition approver decisions are incomplete."))
	if architecture_approval_granted != 1:
		parts.append(_("Architecture Approval checkpoint is not approved."))
	if scope_isolation_confirmed != 1:
		parts.append(_("Mixed-scope rule violation detected; triggered scope is mixed with additive scope and remains blocked."))
	if stop_declaration_complete != 1:
		parts.append(_("Implementation Stop Declaration artifact is incomplete."))
	elif stop_declaration_resolved != 1 and trigger_detected == 1:
		parts.append(_("Implementation Stop Declaration exists but is not formally resolved to the determined disposition."))

	parts.append(
		_("Deterministic disposition outcome: {0}. Implementation authorization remains disabled in Feature 3B planning-only stage.").format(
			final_outcome
		)
	)
	if context.governance_rationale:
		parts.append(context.governance_rationale)
	return " ".join(parts)


def _resolve_baseline_change_context(value: dict[str, Any] | None) -> Feature3BBaselineChangeContext:
	payload = dict(value or {})

	trigger_flags = {field: 0 for field in TRIGGER_RULE_FIELDS}
	provided_flags = payload.get("trigger_flags") or {}
	if provided_flags and not isinstance(provided_flags, dict):
		frappe.throw(_("trigger_flags must be a JSON object of trigger booleans."), exc=frappe.ValidationError)
	for field in TRIGGER_RULE_FIELDS:
		trigger_flags[field] = cint((provided_flags or {}).get(field) or payload.get(field) or 0)

	trigger_codes = payload.get("trigger_codes") or []
	if trigger_codes and not isinstance(trigger_codes, (list, tuple, set)):
		frappe.throw(_("trigger_codes must be a list of trigger field names."), exc=frappe.ValidationError)
	for code in trigger_codes:
		name = str(code or "").strip()
		if name in trigger_flags:
			trigger_flags[name] = 1

	requested_disposition = _normalize_required_text(
		payload.get("requested_disposition", REQUESTED_DISPOSITION_CONTINUE_BLOCKED),
		"Requested Disposition",
	)
	if requested_disposition not in ALLOWED_REQUESTED_DISPOSITIONS:
		frappe.throw(
			_("Requested Disposition is invalid for Feature 3B baseline-change governance."),
			exc=frappe.ValidationError,
		)

	adr_evidence = payload.get("adr_evidence") or {}
	if adr_evidence and not isinstance(adr_evidence, dict):
		frappe.throw(_("adr_evidence must be a JSON object."), exc=frappe.ValidationError)

	approver_decisions_input = payload.get("approver_decisions") or {}
	if approver_decisions_input and not isinstance(approver_decisions_input, dict):
		frappe.throw(_("approver_decisions must be a JSON object."), exc=frappe.ValidationError)
	approver_decisions = {
		role: cint((approver_decisions_input or {}).get(role) or 0)
		for role in GOVERNANCE_ROLES
	}

	stop_declaration = payload.get("stop_declaration") or {}
	if stop_declaration and not isinstance(stop_declaration, dict):
		frappe.throw(_("stop_declaration must be a JSON object."), exc=frappe.ValidationError)

	return Feature3BBaselineChangeContext(
		trigger_flags=trigger_flags,
		requested_disposition=requested_disposition,
		adr_evidence=dict(adr_evidence),
		approver_decisions=approver_decisions,
		architecture_approval_granted=cint(payload.get("architecture_approval_granted") or 0),
		scope_mixed_with_additive=cint(payload.get("scope_mixed_with_additive") or 0),
		stop_declaration=dict(stop_declaration),
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
	text = str(value or "").strip()
	if not text:
		frappe.throw(_("{0} is required.").format(field_label), exc=frappe.ValidationError)
	return text


def _has_reviewable_value(value: Any) -> bool:
	if value is None:
		return False
	if isinstance(value, str):
		return bool(value.strip())
	if isinstance(value, (list, tuple, set, dict)):
		return bool(value)
	return True


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


def _enforce_no_unresolved_runtime_guard_risks() -> None:
	risk_map = _evaluate_runtime_guard_risks()
	unresolved = tuple(sorted(code for code, active in risk_map.items() if active))
	if unresolved:
		frappe.throw(
			_("Feature 3B blocked due to unresolved baseline/runtime guard risks: {0}.").format(", ".join(unresolved)),
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
	if not frappe.db.exists("Report", FEATURE3B_REPORT_NAME):
		return True

	report_roles = set(
		frappe.get_all(
			"Has Role",
			filters={"parent": FEATURE3B_REPORT_NAME, "parenttype": "Report", "parentfield": "roles"},
			pluck="role",
		)
	)
	return report_roles != set(GOVERNANCE_ROLES)


def _detect_runtime_contract_mutation_risk() -> bool:
	report_row = frappe.db.get_value(
		"Report",
		FEATURE3B_REPORT_NAME,
		["report_type", "is_standard", "module", "ref_doctype"],
		as_dict=True,
	)
	if not report_row:
		return True
	if report_row.report_type != "Script Report":
		return True
	if report_row.is_standard != "Yes":
		return True
	if report_row.module != FEATURE3B_REPORT_MODULE:
		return True
	if report_row.ref_doctype != FEATURE3B_REPORT_REF_DOCTYPE:
		return True
	return False


def _item_sort_key(item: Feature3BBaselineChangeGovernanceItem) -> tuple[Any, ...]:
	return (
		item.decision_record,
		item.disposition_outcome,
	)


def _record_actor_trace_audit_evidence(
	*,
	invocation_context: str,
	lighthouse_workflow_charter: str,
	decision_record: str | None,
	review_window_start: date,
	review_window_end: date,
	policy_version: str,
	context: Feature3BBaselineChangeContext,
	items: tuple[Feature3BBaselineChangeGovernanceItem, ...],
) -> None:
	payload = {
		"event": "feature3b_baseline_change_governance_review_executed",
		"actor": frappe.session.user,
		"executed_at": now_datetime().isoformat(),
		"report_invocation_context": invocation_context,
		"governance_review_context": {
			"policy_version": policy_version,
			"requested_disposition": context.requested_disposition,
		},
		"requested_review_window": {
			"start": review_window_start.isoformat(),
			"end": review_window_end.isoformat(),
		},
		"source_charter": lighthouse_workflow_charter,
		"decision_record": decision_record or "",
		"result_count": len(items),
	}
	frappe.logger(FEATURE3B_AUDIT_LOGGER_NAME).info(payload)


def _require_governance_role() -> None:
	roles = set(frappe.get_roles())
	if not roles.intersection(GOVERNANCE_ROLES):
		frappe.throw(
			_("Feature 3B Baseline Change Governance Review requires a governance role."),
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
	"Feature3BBaselineChangeContext",
	"Feature3BBaselineChangeGovernanceItem",
	"evaluate_feature3b_baseline_change_governance",
]
