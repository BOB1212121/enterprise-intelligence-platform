import json

import frappe
from frappe import _

from enterprise_intelligence_platform.feature3b_conditional_baseline_change_governance import (
	evaluate_feature3b_baseline_change_governance,
)


def execute(filters=None):
	filters = frappe._dict(filters or {})
	charter_name = filters.get("lighthouse_workflow_charter")
	if not charter_name:
		frappe.throw(_("Lighthouse Workflow Charter is required."))

	baseline_change_context = _resolve_baseline_change_context(filters.get("baseline_change_context_json"))

	items = evaluate_feature3b_baseline_change_governance(
		lighthouse_workflow_charter=charter_name,
		decision_record=filters.get("decision_record"),
		review_window_start=filters.get("review_window_start"),
		review_window_end=filters.get("review_window_end"),
		policy_version=filters.get("policy_version"),
		baseline_change_context=baseline_change_context,
		invocation_context="query_report_execute",
	)
	return get_columns(), [item.as_dict() for item in items]


def _resolve_baseline_change_context(value):
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
				_("Baseline Change Context (JSON) is invalid JSON: {0}").format(str(exc)),
				exc=frappe.ValidationError,
			)
		if isinstance(parsed, dict):
			return parsed
		frappe.throw(_("Baseline Change Context (JSON) must decode to a JSON object."), exc=frappe.ValidationError)
	frappe.throw(_("Baseline Change Context input type is invalid."), exc=frappe.ValidationError)


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
			"width": 170,
		},
		{
			"label": _("Baseline Change Trigger Detected"),
			"fieldname": "baseline_change_trigger_detected",
			"fieldtype": "Check",
			"width": 220,
		},
		{
			"label": _("Baseline Change Trigger Codes"),
			"fieldname": "baseline_change_trigger_codes",
			"fieldtype": "Small Text",
			"width": 260,
		},
		{
			"label": _("Implementation Stop Required"),
			"fieldname": "implementation_stop_required",
			"fieldtype": "Check",
			"width": 190,
		},
		{
			"label": _("ADR Route Required"),
			"fieldname": "adr_route_required",
			"fieldtype": "Check",
			"width": 150,
		},
		{
			"label": _("ADR Initiation Blocked"),
			"fieldname": "adr_initiation_blocked",
			"fieldtype": "Check",
			"width": 180,
		},
		{
			"label": _("ADR Evidence Complete"),
			"fieldname": "adr_evidence_complete",
			"fieldtype": "Check",
			"width": 160,
		},
		{
			"label": _("Mandatory Disposition Approvals Complete"),
			"fieldname": "mandatory_disposition_approvals_complete",
			"fieldtype": "Check",
			"width": 280,
		},
		{
			"label": _("Architecture Approval Granted"),
			"fieldname": "architecture_approval_granted",
			"fieldtype": "Check",
			"width": 220,
		},
		{
			"label": _("Implementation Stop Declaration Complete"),
			"fieldname": "implementation_stop_declaration_complete",
			"fieldtype": "Check",
			"width": 280,
		},
		{
			"label": _("Implementation Stop Declaration Resolved"),
			"fieldname": "implementation_stop_declaration_resolved",
			"fieldtype": "Check",
			"width": 290,
		},
		{
			"label": _("Disposition Outcome"),
			"fieldname": "disposition_outcome",
			"fieldtype": "Data",
			"width": 240,
		},
		{
			"label": _("Re-entry Planning Authorized"),
			"fieldname": "reentry_planning_authorized",
			"fieldtype": "Check",
			"width": 210,
		},
		{
			"label": _("Implementation Authorized"),
			"fieldname": "implementation_authorized",
			"fieldtype": "Check",
			"width": 190,
		},
		{
			"label": _("Scope Isolation Confirmed"),
			"fieldname": "scope_isolation_confirmed",
			"fieldtype": "Check",
			"width": 190,
		},
		{
			"label": _("Governance Role Confirmed"),
			"fieldname": "governance_role_confirmed",
			"fieldtype": "Check",
			"width": 190,
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
			"width": 340,
		},
	]
