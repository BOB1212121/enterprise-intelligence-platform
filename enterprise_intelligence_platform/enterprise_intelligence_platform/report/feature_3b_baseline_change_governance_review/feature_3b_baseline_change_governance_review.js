frappe.query_reports["Feature 3B Baseline Change Governance Review"] = {
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
			default: "FEATURE3B_POLICY_V1",
		},
		{
			fieldname: "baseline_change_context_json",
			label: __("Baseline Change Context (JSON)"),
			fieldtype: "Small Text",
			description: __(
				"Optional JSON object: trigger_flags/trigger_codes, requested_disposition, adr_evidence, approver_decisions, architecture_approval_granted, scope_mixed_with_additive, stop_declaration, governance_rationale"
			),
		},
	],
};
