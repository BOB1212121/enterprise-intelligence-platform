from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, now_datetime

GOVERNANCE_ROLES = (
	"EIP Workflow Owner",
	"EIP Executive Sponsor",
	"EIP Operations Manager",
	"System Manager",
)

FEATURE3A_REPORT_NAME = "Feature 3A Follow-Through Lifecycle Governance Review"
FEATURE3A_REPORT_MODULE = "Enterprise Intelligence Platform"
FEATURE3A_REPORT_REF_DOCTYPE = "Decision Record"
FEATURE3A_AUDIT_LOGGER_NAME = "enterprise_intelligence_platform.feature3a"

LIFECYCLE_IDENTIFIED = "Identified"
LIFECYCLE_PRIORITIZED = "Prioritized"
LIFECYCLE_IN_PROGRESS = "In Progress"
LIFECYCLE_ESCALATED = "Escalated"
LIFECYCLE_RESOLVED = "Resolved"
LIFECYCLE_CLOSED = "Closed"

ACTION_PRIORITIZE = "Prioritize"
ACTION_START = "Start"
ACTION_ESCALATE = "Escalate"
ACTION_DEESCALATE = "Deescalate"
ACTION_RESOLVE = "Resolve"
ACTION_CLOSE = "Close"

VALID_STATES = {
	LIFECYCLE_IDENTIFIED,
	LIFECYCLE_PRIORITIZED,
	LIFECYCLE_IN_PROGRESS,
	LIFECYCLE_ESCALATED,
	LIFECYCLE_RESOLVED,
	LIFECYCLE_CLOSED,
}

VALID_ACTIONS = {
	ACTION_PRIORITIZE,
	ACTION_START,
	ACTION_ESCALATE,
	ACTION_DEESCALATE,
	ACTION_RESOLVE,
	ACTION_CLOSE,
}

TRANSITION_POLICY = {
	(LIFECYCLE_IDENTIFIED, ACTION_PRIORITIZE): (LIFECYCLE_PRIORITIZED, {"EIP Workflow Owner", "EIP Operations Manager"}),
	(LIFECYCLE_PRIORITIZED, ACTION_START): (LIFECYCLE_IN_PROGRESS, {"EIP Workflow Owner", "EIP Operations Manager"}),
	(LIFECYCLE_IN_PROGRESS, ACTION_ESCALATE): (LIFECYCLE_ESCALATED, {"EIP Operations Manager", "EIP Executive Sponsor"}),
	(LIFECYCLE_ESCALATED, ACTION_DEESCALATE): (LIFECYCLE_IN_PROGRESS, {"EIP Operations Manager", "EIP Executive Sponsor"}),
	(LIFECYCLE_IN_PROGRESS, ACTION_RESOLVE): (LIFECYCLE_RESOLVED, {"EIP Workflow Owner", "EIP Executive Sponsor"}),
	(LIFECYCLE_ESCALATED, ACTION_RESOLVE): (LIFECYCLE_RESOLVED, {"EIP Workflow Owner", "EIP Executive Sponsor"}),
	(LIFECYCLE_RESOLVED, ACTION_CLOSE): (LIFECYCLE_CLOSED, {"EIP Workflow Owner", "EIP Executive Sponsor"}),
}

REQUIRED_CHECKPOINT_CODES = (
	"owner_resolution_note",
	"dependency_mitigation_evidence",
	"attribution_reconciliation_evidence",
)

PROHIBITED_DUPLICATE_PERSISTENCE_DOCTYPES = (
	"Follow Through Item",
	"Follow Through Cycle",
	"Escalation Case",
	"FollowThroughItem",
	"FollowThroughCycle",
	"EscalationCase",
)


@dataclass(frozen=True)
class Feature3ALifecycleContext:
	current_state: str
	requested_action: str
	completed_checkpoints: tuple[str, ...]
	closure_evidence_links: tuple[tuple[str, str], ...]
	manual_escalation_requested: int
	manual_escalation_clear_requested: int
	governance_rationale: str


@dataclass(frozen=True)
class Feature3ALifecycleGovernanceItem:
	lighthouse_workflow_charter: str
	decision_record: str
	review_window_start: str
	review_window_end: str
	policy_version: str
	current_state: str
	requested_action: str
	transition_allowed: int
	next_state: str
	escalation_required: int
	escalation_clear_allowed: int
	resolution_checkpoints_complete: int
	closure_evidence_complete: int
	closure_allowed: int
	baseline_change_trigger_blocked: int
	adr_route_required: int
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
			"current_state": self.current_state,
			"requested_action": self.requested_action,
			"transition_allowed": self.transition_allowed,
			"next_state": self.next_state,
			"escalation_required": self.escalation_required,
			"escalation_clear_allowed": self.escalation_clear_allowed,
			"resolution_checkpoints_complete": self.resolution_checkpoints_complete,
			"closure_evidence_complete": self.closure_evidence_complete,
			"closure_allowed": self.closure_allowed,
			"baseline_change_trigger_blocked": self.baseline_change_trigger_blocked,
			"adr_route_required": self.adr_route_required,
			"governance_role_confirmed": self.governance_role_confirmed,
			"read_only_confirmed": self.read_only_confirmed,
			"ranking_rationale": self.ranking_rationale,
		}


def evaluate_feature3a_lifecycle_governance(
	*,
	lighthouse_workflow_charter: str,
	review_window_start: str,
	review_window_end: str,
	policy_version: str,
	decision_record: str | None = None,
	lifecycle_context: dict[str, Any] | None = None,
	invocation_context: str = "direct_helper_call",
) -> tuple[Feature3ALifecycleGovernanceItem, ...]:
	roles = _require_governance_role()
	_require_read_permissions()
	baseline_change_trigger_blocked, adr_route_required, unresolved_triggers = _evaluate_baseline_change_governance_signal()
	if baseline_change_trigger_blocked == 1:
		frappe.throw(
			_(
				"Feature 3A blocked due to unresolved Baseline Change triggers: {0}. "
				"adr_route_required=1 baseline_change_trigger_blocked=1"
			).format(", ".join(unresolved_triggers)),
			exc=frappe.ValidationError,
		)

	window_start, window_end = _validate_review_window(review_window_start, review_window_end)
	policy_version_text = _normalize_required_text(policy_version, "Policy Version")
	context = _resolve_lifecycle_context(lifecycle_context)

	decision_rows = _fetch_decision_docs(lighthouse_workflow_charter, decision_record)
	items: list[Feature3ALifecycleGovernanceItem] = []
	for decision in decision_rows:
		items.append(
			_build_lifecycle_item(
				decision=decision,
				window_start=window_start,
				window_end=window_end,
				policy_version=policy_version_text,
				context=context,
				roles=roles,
				baseline_change_trigger_blocked=baseline_change_trigger_blocked,
				adr_route_required=adr_route_required,
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


def _build_lifecycle_item(
	*,
	decision: dict[str, Any],
	window_start: date,
	window_end: date,
	policy_version: str,
	context: Feature3ALifecycleContext,
	roles: set[str],
	baseline_change_trigger_blocked: int,
	adr_route_required: int,
) -> Feature3ALifecycleGovernanceItem:
	escalation_required = _evaluate_escalation_required(
		decision_name=decision.get("name"),
		window_start=window_start,
		window_end=window_end,
	)
	resolution_checkpoints_complete = _evaluate_resolution_checkpoints_complete(context)
	closure_evidence_complete = _evaluate_closure_evidence_complete(
		decision_name=decision.get("name"),
		charter_name=decision.get("lighthouse_workflow_charter"),
		links=context.closure_evidence_links,
	)

	next_state, role_allowed, transition_rationale = _evaluate_transition(
		current_state=context.current_state,
		requested_action=context.requested_action,
		roles=roles,
	)

	escalation_clear_allowed = (
		1
		if escalation_required == 0
		and cint(context.manual_escalation_clear_requested) == 1
		and resolution_checkpoints_complete == 1
		else 0
	)
	closure_allowed = 1 if (
		next_state == LIFECYCLE_CLOSED
		and role_allowed == 1
		and escalation_required == 0
		and resolution_checkpoints_complete == 1
		and closure_evidence_complete == 1
	) else 0

	if context.requested_action == ACTION_CLOSE and closure_allowed != 1:
		role_allowed = 0
		next_state = context.current_state
		transition_rationale = _(
			"Closure blocked: closure requires no active escalation, complete checkpoints, and complete closure evidence."
		)

	if context.requested_action == ACTION_ESCALATE and cint(context.manual_escalation_requested) == 0 and escalation_required == 0:
		role_allowed = 0
		next_state = context.current_state
		transition_rationale = _("Escalation blocked: no escalation trigger or manual escalation request.")

	if context.requested_action == ACTION_DEESCALATE and escalation_clear_allowed != 1:
		role_allowed = 0
		next_state = context.current_state
		transition_rationale = _("De-escalation blocked: escalation risk remains or clear request missing.")

	rationale = " ".join(
		part
		for part in (
			transition_rationale,
			context.governance_rationale,
		)
		if part
	)

	return Feature3ALifecycleGovernanceItem(
		lighthouse_workflow_charter=decision.get("lighthouse_workflow_charter"),
		decision_record=decision.get("name"),
		review_window_start=window_start.isoformat(),
		review_window_end=window_end.isoformat(),
		policy_version=policy_version,
		current_state=context.current_state,
		requested_action=context.requested_action,
		transition_allowed=role_allowed,
		next_state=next_state,
		escalation_required=escalation_required,
		escalation_clear_allowed=escalation_clear_allowed,
		resolution_checkpoints_complete=resolution_checkpoints_complete,
		closure_evidence_complete=closure_evidence_complete,
		closure_allowed=closure_allowed,
		baseline_change_trigger_blocked=baseline_change_trigger_blocked,
		adr_route_required=adr_route_required,
		governance_role_confirmed=1,
		read_only_confirmed=1,
		ranking_rationale=rationale,
	)


def _evaluate_transition(*, current_state: str, requested_action: str, roles: set[str]) -> tuple[str, int, str]:
	policy = TRANSITION_POLICY.get((current_state, requested_action))
	if not policy:
		return current_state, 0, _("Requested transition is invalid for the current lifecycle state.")
	next_state, allowed_roles = policy
	if roles.intersection(allowed_roles):
		return next_state, 1, _("Transition allowed for the active governance role set.")
	return current_state, 0, _("Transition blocked: active user role is not authorized for this transition.")


def _evaluate_escalation_required(*, decision_name: str, window_start: date, window_end: date) -> int:
	dependencies = frappe.get_list(
		"Dependency Exception Record",
		filters={"decision_record": decision_name},
		fields=["dependency_status", "dependency_criticality", "exception_required", "target_resolution_date"],
	)
	for dependency in dependencies:
		if dependency.get("dependency_status") == "Resolved":
			continue
		if not _is_within_window(dependency.get("target_resolution_date"), window_start, window_end):
			continue
		if dependency.get("dependency_criticality") in {"Critical", "High"}:
			return 1
		if cint(dependency.get("exception_required")) == 1:
			return 1

	attribution_rows = frappe.get_list(
		"Attribution Case",
		filters={"decision_record": decision_name},
		fields=["confidence_score", "observation_end_date"],
	)
	for row in attribution_rows:
		if not _is_within_window(row.get("observation_end_date"), window_start, window_end):
			continue
		if flt(row.get("confidence_score") or 0) < 0.70:
			return 1
	return 0


def _evaluate_resolution_checkpoints_complete(context: Feature3ALifecycleContext) -> int:
	return 1 if all(code in context.completed_checkpoints for code in REQUIRED_CHECKPOINT_CODES) else 0


def _evaluate_closure_evidence_complete(
	*,
	decision_name: str,
	charter_name: str,
	links: tuple[tuple[str, str], ...],
) -> int:
	if not links:
		return 0

	for source_doctype, source_name in links:
		if source_doctype == "Decision Record":
			row = frappe.db.get_value(
				"Decision Record",
				source_name,
				["name", "lighthouse_workflow_charter"],
				as_dict=True,
			)
			if not row or row.name != decision_name or row.lighthouse_workflow_charter != charter_name:
				return 0
		elif source_doctype == "Dependency Exception Record":
			row = frappe.db.get_value(
				"Dependency Exception Record",
				source_name,
				["decision_record", "lighthouse_workflow_charter"],
				as_dict=True,
			)
			if not row or row.decision_record != decision_name or row.lighthouse_workflow_charter != charter_name:
				return 0
		elif source_doctype == "Attribution Case":
			row = frappe.db.get_value(
				"Attribution Case",
				source_name,
				["decision_record", "lighthouse_workflow_charter"],
				as_dict=True,
			)
			if not row or row.decision_record != decision_name or row.lighthouse_workflow_charter != charter_name:
				return 0
		else:
			return 0
	return 1


def _record_actor_trace_audit_evidence(
	*,
	invocation_context: str,
	lighthouse_workflow_charter: str,
	decision_record: str | None,
	review_window_start: date,
	review_window_end: date,
	policy_version: str,
	context: Feature3ALifecycleContext,
	items: tuple[Feature3ALifecycleGovernanceItem, ...],
) -> None:
	payload = {
		"event": "feature3a_lifecycle_governance_review_executed",
		"actor": frappe.session.user,
		"executed_at": now_datetime().isoformat(),
		"report_invocation_context": invocation_context,
		"governance_review_context": {
			"policy_version": policy_version,
			"current_state": context.current_state,
			"requested_action": context.requested_action,
		},
		"requested_review_window": {
			"start": review_window_start.isoformat(),
			"end": review_window_end.isoformat(),
		},
		"source_charter": lighthouse_workflow_charter,
		"decision_record": decision_record or "",
		"result_count": len(items),
	}
	frappe.logger(FEATURE3A_AUDIT_LOGGER_NAME).info(payload)


def _item_sort_key(item: Feature3ALifecycleGovernanceItem) -> tuple[Any, ...]:
	return (
		item.decision_record,
		item.current_state,
		item.requested_action,
	)


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


def _resolve_lifecycle_context(value: dict[str, Any] | None) -> Feature3ALifecycleContext:
	payload = dict(value or {})
	current_state = _normalize_required_text(payload.get("current_state", LIFECYCLE_IDENTIFIED), "Current State")
	requested_action = _normalize_required_text(payload.get("requested_action", ACTION_PRIORITIZE), "Requested Action")
	if current_state not in VALID_STATES:
		frappe.throw(_("Current State is invalid for Feature 3A lifecycle governance."), exc=frappe.ValidationError)
	if requested_action not in VALID_ACTIONS:
		frappe.throw(_("Requested Action is invalid for Feature 3A lifecycle governance."), exc=frappe.ValidationError)

	completed = payload.get("completed_checkpoints") or []
	if not isinstance(completed, (list, tuple, set)):
		frappe.throw(_("completed_checkpoints must be a list of checkpoint codes."), exc=frappe.ValidationError)
	completed_checkpoints = tuple(sorted(str(x).strip() for x in completed if str(x).strip()))

	links_input = payload.get("closure_evidence_links") or []
	if not isinstance(links_input, (list, tuple)):
		frappe.throw(_("closure_evidence_links must be a list of [doctype, name] pairs."), exc=frappe.ValidationError)

	links: list[tuple[str, str]] = []
	for row in links_input:
		if not isinstance(row, (list, tuple)) or len(row) != 2:
			frappe.throw(
				_("closure_evidence_links entries must each be [source_doctype, source_name]."),
				exc=frappe.ValidationError,
			)
		source_doctype = str(row[0] or "").strip()
		source_name = str(row[1] or "").strip()
		if not source_doctype or not source_name:
			frappe.throw(
				_("closure_evidence_links entries must include source_doctype and source_name."),
				exc=frappe.ValidationError,
			)
		links.append((source_doctype, source_name))

	return Feature3ALifecycleContext(
		current_state=current_state,
		requested_action=requested_action,
		completed_checkpoints=completed_checkpoints,
		closure_evidence_links=tuple(sorted(links)),
		manual_escalation_requested=cint(payload.get("manual_escalation_requested") or 0),
		manual_escalation_clear_requested=cint(payload.get("manual_escalation_clear_requested") or 0),
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


def _is_within_window(value: Any, window_start: date, window_end: date) -> bool:
	if not value:
		return True
	current = getdate(value)
	return window_start <= current <= window_end


def _enforce_no_unresolved_baseline_change_triggers() -> None:
	triggers = _evaluate_migration_triggers()
	unresolved = tuple(sorted(trigger for trigger, active in triggers.items() if active))
	if unresolved:
		frappe.throw(
			_("Feature 3A blocked due to unresolved Baseline Change triggers: {0}.").format(", ".join(unresolved)),
			exc=frappe.ValidationError,
		)


def _evaluate_migration_triggers() -> dict[str, bool]:
	return {
		"duplicate_source_of_truth_persistence_risk": _detect_duplicate_source_of_truth_persistence_risk(),
		"ownership_mapping_mutation_risk": _detect_ownership_mapping_mutation_risk(),
		"runtime_contract_mutation_risk": _detect_runtime_contract_mutation_risk(),
	}


def _evaluate_baseline_change_governance_signal() -> tuple[int, int, tuple[str, ...]]:
	triggers = _evaluate_migration_triggers()
	unresolved = tuple(sorted(trigger for trigger, active in triggers.items() if active))
	if unresolved:
		return 1, 1, unresolved
	return 0, 0, tuple()


def _detect_duplicate_source_of_truth_persistence_risk() -> bool:
	for doctype_name in PROHIBITED_DUPLICATE_PERSISTENCE_DOCTYPES:
		if frappe.db.exists("DocType", doctype_name):
			return True
	return False


def _detect_ownership_mapping_mutation_risk() -> bool:
	if not frappe.db.exists("Report", FEATURE3A_REPORT_NAME):
		return True

	report_roles = set(
		frappe.get_all(
			"Has Role",
			filters={"parent": FEATURE3A_REPORT_NAME, "parenttype": "Report", "parentfield": "roles"},
			pluck="role",
		)
	)
	return report_roles != set(GOVERNANCE_ROLES)


def _detect_runtime_contract_mutation_risk() -> bool:
	report_row = frappe.db.get_value(
		"Report",
		FEATURE3A_REPORT_NAME,
		["report_type", "is_standard", "module", "ref_doctype"],
		as_dict=True,
	)
	if not report_row:
		return True
	if report_row.report_type != "Script Report":
		return True
	if report_row.is_standard != "Yes":
		return True
	if report_row.module != FEATURE3A_REPORT_MODULE:
		return True
	if report_row.ref_doctype != FEATURE3A_REPORT_REF_DOCTYPE:
		return True
	return False


def _require_governance_role() -> set[str]:
	roles = set(frappe.get_roles())
	if not roles.intersection(GOVERNANCE_ROLES):
		frappe.throw(
			_("Feature 3A lifecycle governance review requires a governance role."),
			exc=frappe.PermissionError,
		)
	return roles


def _require_read_permissions() -> None:
	for doctype in (
		"Lighthouse Workflow Charter",
		"Decision Record",
		"Dependency Exception Record",
		"Attribution Case",
	):
		frappe.has_permission(doctype, ptype="read", throw=True)


__all__ = [
	"Feature3ALifecycleContext",
	"Feature3ALifecycleGovernanceItem",
	"evaluate_feature3a_lifecycle_governance",
]
