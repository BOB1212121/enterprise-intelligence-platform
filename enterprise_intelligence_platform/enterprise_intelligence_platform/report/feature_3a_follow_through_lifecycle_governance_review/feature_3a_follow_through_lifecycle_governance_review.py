import json

import frappe
from frappe import _

from enterprise_intelligence_platform.feature3a_follow_through_lifecycle_orchestration import (
	evaluate_feature3a_lifecycle_governance,
)


def execute(filters=None):
	filters = frappe._dict(filters or {})
	charter_name = filters.get("lighthouse_workflow_charter")
	if not charter_name:
		frappe.throw(_("Lighthouse Workflow Charter is required."))

	lifecycle_context = _resolve_lifecycle_context(filters.get("lifecycle_context_json"))

	items = evaluate_feature3a_lifecycle_governance(
		lighthouse_workflow_charter=charter_name,
		decision_record=filters.get("decision_record"),
		review_window_start=filters.get("review_window_start"),
		review_window_end=filters.get("review_window_end"),
		policy_version=filters.get("policy_version"),
		lifecycle_context=lifecycle_context,
		invocation_context="query_report_execute",
	)
	return get_columns(), [item.as_dict() for item in items]


def _resolve_lifecycle_context(value):
	if value is None:
		return {}
	if isinstance(value, dict):
		return value
	if isinstance(value, str):
		text = value.strip()
		if not text:
			return {}
		try:
			parsed = json.loads(text)
		except json.JSONDecodeError as exc:
			frappe.throw(
				_("Lifecycle Context (JSON) is invalid JSON: {0}").format(str(exc)),
				exc=frappe.ValidationError,
			)
		if isinstance(parsed, dict):
			return parsed
		frappe.throw(_("Lifecycle Context (JSON) must decode to a JSON object."), exc=frappe.ValidationError)
	frappe.throw(_("Lifecycle Context input type is invalid."), exc=frappe.ValidationError)


def get_columns():
	return [
		{
			"label": _("Lighthouse Workflow Charter"),
			"fieldname": "lighthouse_workflow_charter",
			"fieldtype": "Link",
			"options": "Lighthouse Workflow Charter",
			"width": 180,
		},
		{
			"label": _("Decision Record"),
			"fieldname": "decision_record",
			"fieldtype": "Link",
			"options": "Decision Record",
			"width": 160,
		},
		{
			"label": _("Review Window Start"),
			"fieldname": "review_window_start",
			"fieldtype": "Date",
			"width": 130,
		},
		{
			"label": _("Review Window End"),
			"fieldname": "review_window_end",
			"fieldtype": "Date",
			"width": 130,
		},
		{
			"label": _("Policy Version"),
			"fieldname": "policy_version",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Current State"),
			"fieldname": "current_state",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"label": _("Requested Action"),
			"fieldname": "requested_action",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Transition Allowed"),
			"fieldname": "transition_allowed",
			"fieldtype": "Check",
			"width": 140,
		},
		{
			"label": _("Next State"),
			"fieldname": "next_state",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"label": _("Escalation Required"),
			"fieldname": "escalation_required",
			"fieldtype": "Check",
			"width": 150,
		},
		{
			"label": _("Escalation Clear Allowed"),
			"fieldname": "escalation_clear_allowed",
			"fieldtype": "Check",
			"width": 170,
		},
		{
			"label": _("Resolution Checkpoints Complete"),
			"fieldname": "resolution_checkpoints_complete",
			"fieldtype": "Check",
			"width": 220,
		},
		{
			"label": _("Closure Evidence Complete"),
			"fieldname": "closure_evidence_complete",
			"fieldtype": "Check",
			"width": 190,
		},
		{
			"label": _("Closure Allowed"),
			"fieldname": "closure_allowed",
			"fieldtype": "Check",
			"width": 130,
		},
		{
			"label": _("Baseline Change Trigger Blocked"),
			"fieldname": "baseline_change_trigger_blocked",
			"fieldtype": "Check",
			"width": 220,
		},
		{
			"label": _("ADR Route Required"),
			"fieldname": "adr_route_required",
			"fieldtype": "Check",
			"width": 150,
		},
		{
			"label": _("Governance Role Confirmed"),
			"fieldname": "governance_role_confirmed",
			"fieldtype": "Check",
			"width": 180,
		},
		{
			"label": _("Read Only Confirmed"),
			"fieldname": "read_only_confirmed",
			"fieldtype": "Check",
			"width": 150,
		},
		{
			"label": _("Governance Rationale"),
			"fieldname": "ranking_rationale",
			"fieldtype": "Small Text",
			"width": 320,
		},
	]
