import frappe

ROLES = ["EIP Workflow Owner", "EIP Executive Sponsor", "EIP Operations Manager"]
WORKFLOW_NAME = "Decision Record Approval"
TARGET_DOCTYPE = "Decision Record"
WORKFLOW_STATES = ["Draft", "Submitted for Approval", "Approved", "Rejected"]
WORKFLOW_ACTIONS = ["Submit", "Approve", "Reject", "Revise"]


def execute():
	ensure_roles()
	ensure_workflow_states()
	ensure_workflow_actions()
	ensure_workflow()


def ensure_roles():
	for role_name in ROLES:
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert(ignore_permissions=True)


def ensure_workflow_states():
	for state_name in WORKFLOW_STATES:
		if not frappe.db.exists("Workflow State", state_name):
			frappe.get_doc(
				{
					"doctype": "Workflow State",
					"workflow_state_name": state_name,
					"style": "Primary",
				}
			).insert(ignore_permissions=True)


def ensure_workflow_actions():
	for action_name in WORKFLOW_ACTIONS:
		if not frappe.db.exists("Workflow Action Master", action_name):
			frappe.get_doc(
				{
					"doctype": "Workflow Action Master",
					"workflow_action_name": action_name,
				}
			).insert(ignore_permissions=True)


def ensure_workflow():
	for workflow_name in frappe.get_all("Workflow", filters={"document_type": TARGET_DOCTYPE}, pluck="name"):
		if workflow_name != WORKFLOW_NAME:
			frappe.db.set_value("Workflow", workflow_name, "is_active", 0)

	if frappe.db.exists("Workflow", WORKFLOW_NAME):
		frappe.delete_doc("Workflow", WORKFLOW_NAME, force=1, ignore_permissions=True)

	workflow = frappe.new_doc("Workflow")
	workflow.workflow_name = WORKFLOW_NAME
	workflow.document_type = TARGET_DOCTYPE
	workflow.workflow_state_field = "approval_state"
	workflow.is_active = 1
	workflow.send_email_alert = 0

	workflow.append("states", {"state": "Draft", "doc_status": "0", "allow_edit": "EIP Workflow Owner"})
	workflow.append(
		"states",
		{"state": "Submitted for Approval", "doc_status": "0", "allow_edit": "EIP Executive Sponsor"},
	)
	workflow.append("states", {"state": "Approved", "doc_status": "0", "allow_edit": "System Manager"})
	workflow.append("states", {"state": "Rejected", "doc_status": "0", "allow_edit": "EIP Workflow Owner"})

	workflow.append(
		"transitions",
		{
			"state": "Draft",
			"action": "Submit",
			"next_state": "Submitted for Approval",
			"allowed": "EIP Workflow Owner",
			"allow_self_approval": 1,
		},
	)
	workflow.append(
		"transitions",
		{
			"state": "Submitted for Approval",
			"action": "Approve",
			"next_state": "Approved",
			"allowed": "EIP Executive Sponsor",
			"allow_self_approval": 1,
			"condition": "doc.executive_sponsor == frappe.session.user",
		},
	)
	workflow.append(
		"transitions",
		{
			"state": "Submitted for Approval",
			"action": "Reject",
			"next_state": "Rejected",
			"allowed": "EIP Executive Sponsor",
			"allow_self_approval": 1,
			"condition": "doc.executive_sponsor == frappe.session.user and doc.decision_note",
		},
	)
	workflow.append(
		"transitions",
		{
			"state": "Rejected",
			"action": "Revise",
			"next_state": "Draft",
			"allowed": "EIP Workflow Owner",
			"allow_self_approval": 1,
		},
	)

	workflow.insert(ignore_permissions=True)
