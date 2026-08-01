frappe.query_reports["Feature 3A Follow-Through Lifecycle Governance Review"] = {
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
			default: frappe.datetime.add_days(frappe.datetime.get_today(), -30),
		},
		{
			fieldname: "review_window_end",
			label: __("Review Window End"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.add_days(frappe.datetime.get_today(), 30),
		},
		{
			fieldname: "policy_version",
			label: __("Policy Version"),
			fieldtype: "Data",
			reqd: 1,
			default: "FEATURE3A_POLICY_V1",
		},
		{
			fieldname: "lifecycle_context_json",
			label: __("Lifecycle Context (JSON)"),
			fieldtype: "Small Text",
			description: __(
				"Optional JSON object: current_state, requested_action, completed_checkpoints, closure_evidence_links, manual_escalation_requested, manual_escalation_clear_requested, governance_rationale"
			),
		},
	],
};
