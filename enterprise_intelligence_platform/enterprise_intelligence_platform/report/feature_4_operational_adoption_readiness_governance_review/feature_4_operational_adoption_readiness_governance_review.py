import json

import frappe
from frappe import _

from enterprise_intelligence_platform.feature4_operational_adoption_readiness_governance import (
	evaluate_feature4_readiness_governance,
)


def execute(filters=None):
	filters = frappe._dict(filters or {})
	charter_name = filters.get("lighthouse_workflow_charter")
	if not charter_name:
		frappe.throw(_("Lighthouse Workflow Charter is required."))

	readiness_context = _resolve_readiness_context(filters.get("readiness_context_json"))

	items = evaluate_feature4_readiness_governance(
		lighthouse_workflow_charter=charter_name,
		decision_record=filters.get("decision_record"),
		review_window_start=filters.get("review_window_start"),
		review_window_end=filters.get("review_window_end"),
		policy_version=filters.get("policy_version"),
		readiness_context=readiness_context,
		invocation_context="query_report_execute",
	)
	return get_columns(), [item.as_dict() for item in items]


def _resolve_readiness_context(value):
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
				_("Readiness Context (JSON) is invalid JSON: {0}").format(str(exc)),
				exc=frappe.ValidationError,
			)
		if isinstance(parsed, dict):
			return parsed
		frappe.throw(_("Readiness Context (JSON) must decode to a JSON object."), exc=frappe.ValidationError)
	frappe.throw(_("Readiness Context input type is invalid."), exc=frappe.ValidationError)


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
			"label": _("Readiness Outcome"),
			"fieldname": "readiness_outcome",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Implementation Authorized"),
			"fieldname": "implementation_authorized",
			"fieldtype": "Check",
			"width": 170,
		},
		{
			"label": _("ADR Route Required"),
			"fieldname": "adr_route_required",
			"fieldtype": "Check",
			"width": 150,
		},
		{
			"label": _("Baseline Change Trigger Detected"),
			"fieldname": "baseline_change_trigger_detected",
			"fieldtype": "Check",
			"width": 220,
		},
		{
			"label": _("Baseline Change Trigger Status"),
			"fieldname": "baseline_change_trigger_status",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("Evidence Completeness %"),
			"fieldname": "evidence_completeness_pct",
			"fieldtype": "Percent",
			"width": 170,
		},
		{
			"label": _("RG-001"),
			"fieldname": "rg_001_evidence_completeness_pass",
			"fieldtype": "Check",
			"width": 80,
		},
		{
			"label": _("RG-002"),
			"fieldname": "rg_002_additive_conformance_pass",
			"fieldtype": "Check",
			"width": 80,
		},
		{
			"label": _("RG-003"),
			"fieldname": "rg_003_baseline_trigger_status_pass",
			"fieldtype": "Check",
			"width": 80,
		},
		{
			"label": _("RG-004"),
			"fieldname": "rg_004_mandatory_approvals_pass",
			"fieldtype": "Check",
			"width": 80,
		},
		{
			"label": _("RG-005"),
			"fieldname": "rg_005_rollback_readiness_pass",
			"fieldtype": "Check",
			"width": 80,
		},
		{
			"label": _("RG-006"),
			"fieldname": "rg_006_incident_response_readiness_pass",
			"fieldtype": "Check",
			"width": 80,
		},
		{
			"label": _("RG-007"),
			"fieldname": "rg_007_regression_coverage_pass",
			"fieldtype": "Check",
			"width": 80,
		},
		{
			"label": _("RG-008"),
			"fieldname": "rg_008_traceability_audit_pass",
			"fieldtype": "Check",
			"width": 80,
		},
		{
			"label": _("Gate Sequence Passed"),
			"fieldname": "gate_sequence_passed",
			"fieldtype": "Check",
			"width": 170,
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
			"width": 360,
		},
	]
