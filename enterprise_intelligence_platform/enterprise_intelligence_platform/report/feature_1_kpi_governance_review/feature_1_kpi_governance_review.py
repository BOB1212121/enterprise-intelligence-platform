import frappe
from frappe import _

from enterprise_intelligence_platform.feature1_kpi_governance import evaluate_feature1_review

REPORT_NAME = "Feature 1 KPI Governance Review"
GOVERNANCE_ROLES = (
	"EIP Workflow Owner",
	"EIP Executive Sponsor",
	"EIP Operations Manager",
	"System Manager",
)


def execute(filters=None):
	filters = frappe._dict(filters or {})
	chart_name = filters.get("lighthouse_workflow_charter")
	if not chart_name:
		frappe.throw(_("Lighthouse Workflow Charter is required."))

	_require_governance_role()

	result = evaluate_feature1_review(
		lighthouse_workflow_charter=chart_name,
		decision_record=filters.get("decision_record"),
		candidate_a_score=filters.get("candidate_a_score"),
		candidate_b_score=filters.get("candidate_b_score"),
		comparative_weighting_model=filters.get("comparative_weighting_model"),
		governance_package=filters.get("governance_package_json"),
		baseline_change_trigger=filters.get("baseline_change_trigger"),
	)
	return get_columns(), [result.as_dict()]


def _require_governance_role():
	roles = set(frappe.get_roles())
	if not roles.intersection(GOVERNANCE_ROLES):
		frappe.throw(_("Feature 1 KPI Governance Review requires a governance role."), exc=frappe.PermissionError)


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
			"label": _("Weighted Candidate A Score"),
			"fieldname": "weighted_candidate_a_score",
			"fieldtype": "Float",
			"width": 130,
		},
		{
			"label": _("Weighted Candidate B Score"),
			"fieldname": "weighted_candidate_b_score",
			"fieldtype": "Float",
			"width": 130,
		},
		{
			"label": _("Comparative Weighting Model"),
			"fieldname": "comparative_weighting_model",
			"fieldtype": "Data",
			"width": 210,
		},
		{
			"label": _("KPI Completeness %"),
			"fieldname": "kpi_completeness_pct",
			"fieldtype": "Float",
			"width": 150,
		},
		{
			"label": _("Evidence Completeness %"),
			"fieldname": "evidence_completeness_pct",
			"fieldtype": "Float",
			"width": 160,
		},
		{
			"label": _("Comparative Delta"),
			"fieldname": "comparative_delta",
			"fieldtype": "Float",
			"width": 130,
		},
		{
			"label": _("Mandatory Evidence Present"),
			"fieldname": "mandatory_evidence_present",
			"fieldtype": "Int",
			"width": 170,
		},
		{
			"label": _("Mandatory Evidence Total"),
			"fieldname": "mandatory_evidence_total",
			"fieldtype": "Int",
			"width": 160,
		},
		{
			"label": _("Missing Evidence Items"),
			"fieldname": "missing_evidence_items",
			"fieldtype": "Small Text",
			"width": 220,
		},
		{
			"label": _("Resolved Dependency Count"),
			"fieldname": "resolved_dependency_count",
			"fieldtype": "Int",
			"width": 160,
		},
		{
			"label": _("Approved Attribution Count"),
			"fieldname": "approved_attribution_count",
			"fieldtype": "Int",
			"width": 160,
		},
		{
			"label": _("Unresolved High/Critical Findings"),
			"fieldname": "unresolved_high_critical_count",
			"fieldtype": "Int",
			"width": 180,
		},
		{
			"label": _("Baseline Compatibility Confirmed"),
			"fieldname": "baseline_compatibility_confirmed",
			"fieldtype": "Check",
			"width": 180,
		},
		{
			"label": _("Baseline Change Trigger"),
			"fieldname": "baseline_change_trigger",
			"fieldtype": "Check",
			"width": 140,
		},
		{
			"label": _("Approver Unanimity Confirmed"),
			"fieldname": "approver_unanimity_confirmed",
			"fieldtype": "Check",
			"width": 180,
		},
		{
			"label": _("Approved Approver Roles"),
			"fieldname": "approved_approver_roles",
			"fieldtype": "Small Text",
			"width": 220,
		},
		{
			"label": _("Missing Approver Roles"),
			"fieldname": "missing_approver_roles",
			"fieldtype": "Small Text",
			"width": 220,
		},
		{
			"label": _("Review Band Flag"),
			"fieldname": "review_band_flag",
			"fieldtype": "Check",
			"width": 120,
		},
		{
			"label": _("Review Outcome"),
			"fieldname": "review_outcome",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Adjudication Reason"),
			"fieldname": "adjudication_reason",
			"fieldtype": "Small Text",
			"width": 260,
		},
	]
