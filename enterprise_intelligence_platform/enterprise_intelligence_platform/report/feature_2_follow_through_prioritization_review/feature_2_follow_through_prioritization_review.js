frappe.query_reports["Feature 2 Follow-Through Prioritization Review"] = {
	filters: [
		{
			fieldname: "lighthouse_workflow_charter",
			label: __("Lighthouse Workflow Charter"),
			fieldtype: "Link",
			options: "Lighthouse Workflow Charter",
			reqd: 1,
		},
		{
			fieldname: "decision_record",
			label: __("Decision Record"),
			fieldtype: "Link",
			options: "Decision Record",
		},
		{
			fieldname: "review_window_start",
			label: __("Review Window Start"),
			fieldtype: "Date",
			reqd: 1,
		},
		{
			fieldname: "review_window_end",
			label: __("Review Window End"),
			fieldtype: "Date",
			reqd: 1,
		},
		{
			fieldname: "policy_version",
			label: __("Policy Version"),
			fieldtype: "Data",
			default: "FEATURE2_POLICY_V1",
			reqd: 1,
		},
		{
			fieldname: "acceptance_parameters_json",
			label: __("Acceptance Parameters (JSON)"),
			fieldtype: "Small Text",
			description: __(
				"Optional JSON override for named performance acceptance parameters; defaults use approved named parameter identifiers."
			),
		},
	],
};
