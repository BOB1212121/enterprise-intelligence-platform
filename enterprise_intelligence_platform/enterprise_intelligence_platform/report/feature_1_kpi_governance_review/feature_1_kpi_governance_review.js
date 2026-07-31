frappe.query_reports["Feature 1 KPI Governance Review"] = {
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
			fieldname: "candidate_a_score",
			label: __("Candidate A Score"),
			fieldtype: "Float",
		},
		{
			fieldname: "candidate_b_score",
			label: __("Candidate B Score"),
			fieldtype: "Float",
		},
		{
			fieldname: "comparative_weighting_model",
			label: __("Comparative Weighting Model"),
			fieldtype: "Data",
		},
	],
};
