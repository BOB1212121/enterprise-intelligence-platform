import json

import frappe
from frappe import _

from enterprise_intelligence_platform.feature2_follow_through_orchestration import (
	evaluate_feature2_prioritization,
)


def execute(filters=None):
	filters = frappe._dict(filters or {})
	charter_name = filters.get("lighthouse_workflow_charter")
	if not charter_name:
		frappe.throw(_("Lighthouse Workflow Charter is required."))

	acceptance_parameters = _resolve_acceptance_parameters(filters.get("acceptance_parameters_json"))

	items = evaluate_feature2_prioritization(
		lighthouse_workflow_charter=charter_name,
		decision_record=filters.get("decision_record"),
		review_window_start=filters.get("review_window_start"),
		review_window_end=filters.get("review_window_end"),
		policy_version=filters.get("policy_version"),
		acceptance_parameters=acceptance_parameters,
		invocation_context="query_report_execute",
	)
	return get_columns(), [item.as_dict() for item in items]


def _resolve_acceptance_parameters(value):
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
				_("Acceptance Parameters (JSON) is invalid JSON: {0}").format(str(exc)),
				exc=frappe.ValidationError,
			)
		if isinstance(parsed, dict):
			return parsed
		frappe.throw(_("Acceptance Parameters (JSON) must decode to a JSON object."), exc=frappe.ValidationError)
	frappe.throw(_("Acceptance Parameters input type is invalid."), exc=frappe.ValidationError)


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
			"label": _("Item Type"),
			"fieldname": "item_type",
			"fieldtype": "Data",
			"width": 170,
		},
		{
			"label": _("Item Title"),
			"fieldname": "item_title",
			"fieldtype": "Data",
			"width": 260,
		},
		{
			"label": _("Source DocType"),
			"fieldname": "source_doctype",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Source Name"),
			"fieldname": "source_name",
			"fieldtype": "Dynamic Link",
			"options": "source_doctype",
			"width": 180,
		},
		{
			"label": _("Source Owner"),
			"fieldname": "source_owner",
			"fieldtype": "Link",
			"options": "User",
			"width": 150,
		},
		{
			"label": _("Executive Sponsor"),
			"fieldname": "executive_sponsor",
			"fieldtype": "Link",
			"options": "User",
			"width": 150,
		},
		{
			"label": _("Priority Score"),
			"fieldname": "priority_score",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Priority Band"),
			"fieldname": "priority_band",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Urgency Bucket"),
			"fieldname": "urgency_bucket",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Source Link Integrity Confirmed"),
			"fieldname": "source_link_integrity_confirmed",
			"fieldtype": "Check",
			"width": 200,
		},
		{
			"label": _("Read Only Confirmed"),
			"fieldname": "read_only_confirmed",
			"fieldtype": "Check",
			"width": 150,
		},
		{
			"label": _("Non-Duplication Boundary Confirmed"),
			"fieldname": "non_duplication_boundary_confirmed",
			"fieldtype": "Check",
			"width": 230,
		},
		{
			"label": _("Ranking Rationale"),
			"fieldname": "ranking_rationale",
			"fieldtype": "Small Text",
			"width": 280,
		},
		{
			"label": _("PERF_MAX_RANKING_EXECUTION_DURATION"),
			"fieldname": "perf_max_ranking_execution_duration",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("PERF_MIN_ITEMS_PER_REVIEW_WINDOW"),
			"fieldname": "perf_min_items_per_review_window",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("PERF_ORDERING_STABILITY_TOLERANCE"),
			"fieldname": "perf_ordering_stability_tolerance",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("PERF_SUPPORTED_RANKING_DATASET_PROFILE"),
			"fieldname": "perf_supported_ranking_dataset_profile",
			"fieldtype": "Data",
			"width": 250,
		},
		{
			"label": _("PERF_DEGRADATION_POLICY_ON_CAPACITY_EXCEEDED"),
			"fieldname": "perf_degradation_policy_on_capacity_exceeded",
			"fieldtype": "Data",
			"width": 280,
		},
		{
			"label": _("PERF_SUPPORTED_REVIEW_WINDOW_DEFINITION"),
			"fieldname": "perf_supported_review_window_definition",
			"fieldtype": "Data",
			"width": 260,
		},
	]
