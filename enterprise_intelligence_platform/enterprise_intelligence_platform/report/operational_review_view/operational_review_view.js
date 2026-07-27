frappe.query_reports["Operational Review View"] = {
	filters: [
		{
			fieldname: "executive_sponsor",
			label: __("Executive Sponsor"),
			fieldtype: "Link",
			options: "User"
		},
		{
			fieldname: "workflow_owner",
			label: __("Workflow Owner"),
			fieldtype: "Link",
			options: "User"
		},
		{
			fieldname: "lighthouse_workflow_charter",
			label: __("Lighthouse Workflow Charter"),
			fieldtype: "Link",
			options: "Lighthouse Workflow Charter"
		},
		{
			fieldname: "decision_record",
			label: __("Decision Record"),
			fieldtype: "Link",
			options: "Decision Record"
		},
		{
			fieldname: "approval_state",
			label: __("Approval State"),
			fieldtype: "Select",
			options: "\nDraft\nSubmitted for Approval\nApproved\nRejected"
		},
		{
			fieldname: "dependency_status",
			label: __("Dependency Status"),
			fieldtype: "Select",
			options: "\nOpen\nAt Risk\nResolved"
		},
		{
			fieldname: "dependency_criticality",
			label: __("Dependency Criticality"),
			fieldtype: "Select",
			options: "\nLow\nMedium\nHigh\nCritical"
		},
		{
			fieldname: "exception_required",
			label: __("Exception Required"),
			fieldtype: "Select",
			options: "\nYes\nNo"
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date"
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date"
		},
		{
			fieldname: "show_overdue_only",
			label: __("Show Overdue Only"),
			fieldtype: "Check"
		}
	]
};
