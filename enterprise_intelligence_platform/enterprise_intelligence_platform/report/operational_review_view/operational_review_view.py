from datetime import date

import frappe
from frappe import _
from frappe.query_builder.functions import Count
from frappe.utils import cint, getdate, today

STATUS_RESOLVED = "Resolved"
STATUS_AT_RISK = "At Risk"
STATE_SUBMITTED_FOR_APPROVAL = "Submitted for Approval"

CRITICALITY_RANK = {
	"Critical": 0,
	"High": 1,
	"Medium": 2,
	"Low": 3,
}


def execute(filters=None):
	filters = frappe._dict(filters or {})
	frappe.has_permission("Dependency Exception Record", ptype="read", throw=True)

	columns = get_columns()
	rows = get_rows(filters)
	return columns, rows


def get_columns():
	return [
		{
			"label": _("Dependency Record"),
			"fieldname": "dependency_record",
			"fieldtype": "Link",
			"options": "Dependency Exception Record",
			"width": 180,
		},
		{"label": _("Dependency Title"), "fieldname": "dependency_title", "fieldtype": "Data", "width": 220},
		{
			"label": _("Decision Record"),
			"fieldname": "decision_record",
			"fieldtype": "Link",
			"options": "Decision Record",
			"width": 180,
		},
		{"label": _("Decision Title"), "fieldname": "decision_title", "fieldtype": "Data", "width": 220},
		{
			"label": _("Lighthouse Workflow Charter"),
			"fieldname": "lighthouse_workflow_charter",
			"fieldtype": "Link",
			"options": "Lighthouse Workflow Charter",
			"width": 220,
		},
		{"label": _("Workflow Name"), "fieldname": "workflow_name", "fieldtype": "Data", "width": 220},
		{
			"label": _("Workflow Owner"),
			"fieldname": "workflow_owner",
			"fieldtype": "Link",
			"options": "User",
			"width": 170,
		},
		{
			"label": _("Executive Sponsor"),
			"fieldname": "executive_sponsor",
			"fieldtype": "Link",
			"options": "User",
			"width": 170,
		},
		{
			"label": _("Dependency Approval State"),
			"fieldname": "dependency_approval_state",
			"fieldtype": "Data",
			"width": 190,
		},
		{
			"label": _("Dependency Status"),
			"fieldname": "dependency_status",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Dependency Criticality"),
			"fieldname": "dependency_criticality",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": _("Exception Required"),
			"fieldname": "exception_required",
			"fieldtype": "Check",
			"width": 130,
		},
		{
			"label": _("Exception Expiry Date"),
			"fieldname": "exception_expiry_date",
			"fieldtype": "Date",
			"width": 150,
		},
		{
			"label": _("Declaration Date"),
			"fieldname": "declaration_date",
			"fieldtype": "Date",
			"width": 140,
		},
		{
			"label": _("Target Resolution Date"),
			"fieldname": "target_resolution_date",
			"fieldtype": "Date",
			"width": 160,
		},
		{
			"label": _("Dependency Approved By"),
			"fieldname": "dependency_approved_by",
			"fieldtype": "Link",
			"options": "User",
			"width": 170,
		},
		{
			"label": _("Decision Approval State"),
			"fieldname": "decision_approval_state",
			"fieldtype": "Data",
			"width": 170,
		},
		{
			"label": _("Decision Target Date"),
			"fieldname": "decision_target_date",
			"fieldtype": "Date",
			"width": 150,
		},
		{
			"label": _("Charter Approval State"),
			"fieldname": "charter_approval_state",
			"fieldtype": "Data",
			"width": 170,
		},
		{
			"label": _("Pending Sponsor Action"),
			"fieldname": "pending_sponsor_action",
			"fieldtype": "Check",
			"width": 170,
		},
		{"label": _("Overdue"), "fieldname": "overdue_flag", "fieldtype": "Check", "width": 100},
		{"label": _("At Risk"), "fieldname": "at_risk_flag", "fieldtype": "Check", "width": 100},
		{
			"label": _("Open Exceptions Count"),
			"fieldname": "open_exceptions_count",
			"fieldtype": "Int",
			"width": 170,
		},
	]


def get_rows(filters):
	rows = fetch_dependency_rows(filters)
	open_exception_counts = fetch_open_exception_counts_by_decision()
	today_date = getdate(today())
	show_overdue_only = cint(filters.get("show_overdue_only"))

	result = []
	for row in rows:
		target_resolution_date = row.get("target_resolution_date")
		is_overdue = bool(
			target_resolution_date
			and target_resolution_date < today_date
			and row.get("dependency_status") != STATUS_RESOLVED
		)
		pending_sponsor_action = row.get("dependency_approval_state") == STATE_SUBMITTED_FOR_APPROVAL
		at_risk_flag = row.get("dependency_status") == STATUS_AT_RISK or is_overdue

		if show_overdue_only and not is_overdue:
			continue

		row["pending_sponsor_action"] = cint(pending_sponsor_action)
		row["overdue_flag"] = cint(is_overdue)
		row["at_risk_flag"] = cint(at_risk_flag)
		row["open_exceptions_count"] = open_exception_counts.get(row.get("decision_record"), 0)

		result.append(row)

	result.sort(key=_sort_key)
	return result


def fetch_dependency_rows(filters):
	dependency = frappe.qb.DocType("Dependency Exception Record")
	decision = frappe.qb.DocType("Decision Record")
	charter = frappe.qb.DocType("Lighthouse Workflow Charter")

	query = (
		frappe.qb.from_(dependency)
		.left_join(decision)
		.on(dependency.decision_record == decision.name)
		.left_join(charter)
		.on(dependency.lighthouse_workflow_charter == charter.name)
		.select(
			dependency.name.as_("dependency_record"),
			dependency.dependency_title,
			dependency.decision_record,
			decision.decision_title,
			dependency.lighthouse_workflow_charter,
			charter.workflow_name,
			dependency.accountable_owner.as_("workflow_owner"),
			dependency.executive_sponsor,
			dependency.approval_state.as_("dependency_approval_state"),
			dependency.dependency_status,
			dependency.dependency_criticality,
			dependency.exception_required,
			dependency.exception_expiry_date,
			dependency.declaration_date,
			dependency.target_resolution_date,
			dependency.approved_by.as_("dependency_approved_by"),
			decision.approval_state.as_("decision_approval_state"),
			decision.target_decision_date.as_("decision_target_date"),
			charter.approval_state.as_("charter_approval_state"),
		)
	)

	if filters.get("executive_sponsor"):
		query = query.where(dependency.executive_sponsor == filters.get("executive_sponsor"))

	if filters.get("workflow_owner"):
		query = query.where(dependency.accountable_owner == filters.get("workflow_owner"))

	if filters.get("lighthouse_workflow_charter"):
		query = query.where(
			dependency.lighthouse_workflow_charter == filters.get("lighthouse_workflow_charter")
		)

	if filters.get("decision_record"):
		query = query.where(dependency.decision_record == filters.get("decision_record"))

	if filters.get("approval_state"):
		query = query.where(dependency.approval_state == filters.get("approval_state"))

	if filters.get("dependency_status"):
		query = query.where(dependency.dependency_status == filters.get("dependency_status"))

	if filters.get("dependency_criticality"):
		query = query.where(dependency.dependency_criticality == filters.get("dependency_criticality"))

	exception_required_filter = _normalize_exception_required_filter(filters.get("exception_required"))
	if exception_required_filter is not None:
		query = query.where(dependency.exception_required == exception_required_filter)

	if filters.get("from_date"):
		query = query.where(dependency.target_resolution_date >= getdate(filters.get("from_date")))

	if filters.get("to_date"):
		query = query.where(dependency.target_resolution_date <= getdate(filters.get("to_date")))

	return query.run(as_dict=True)


def fetch_open_exception_counts_by_decision():
	dependency = frappe.qb.DocType("Dependency Exception Record")

	rows = (
		frappe.qb.from_(dependency)
		.select(dependency.decision_record, Count(dependency.name).as_("open_exceptions_count"))
		.where(dependency.exception_required == 1)
		.where(dependency.dependency_status != STATUS_RESOLVED)
		.groupby(dependency.decision_record)
	).run(as_dict=True)

	return {
		row.get("decision_record"): cint(row.get("open_exceptions_count"))
		for row in rows
		if row.get("decision_record")
	}


def _sort_key(row):
	target_resolution_date = row.get("target_resolution_date")
	criticality_rank = CRITICALITY_RANK.get(row.get("dependency_criticality"), 99)
	return (
		target_resolution_date is None,
		target_resolution_date or date.max,
		criticality_rank,
		row.get("dependency_record") or "",
	)


def _normalize_exception_required_filter(value):
	if value is None or value == "":
		return None

	if isinstance(value, str):
		normalized = value.strip().lower()
		if normalized in {"yes", "1", "true"}:
			return 1
		if normalized in {"no", "0", "false"}:
			return 0

	return cint(value)
