import frappe

ROLE_WORKFLOW_OWNER = "EIP Workflow Owner"
ROLE_EXECUTIVE_SPONSOR = "EIP Executive Sponsor"
ROLE_OPERATIONS_MANAGER = "EIP Operations Manager"
ROLE_SYSTEM_MANAGER = "System Manager"

STATE_DRAFT = "Draft"
STATE_SUBMITTED_FOR_SPONSOR_APPROVAL = "Submitted for Sponsor Approval"
STATE_BASELINE_ACCEPTED = "Baseline Accepted"
STATE_BASELINE_REJECTED = "Baseline Rejected"

ACTION_SUBMIT = "Submit"
ACTION_APPROVE = "Approve"
ACTION_REJECT = "Reject"
ACTION_REVIEW = "Review"

ROLES = [ROLE_WORKFLOW_OWNER, ROLE_EXECUTIVE_SPONSOR, ROLE_OPERATIONS_MANAGER]
WORKFLOW_NAME = "Lighthouse Workflow Charter Approval"
TARGET_DOCTYPE = "Lighthouse Workflow Charter"
WORKFLOW_STATES = [
	STATE_DRAFT,
	STATE_SUBMITTED_FOR_SPONSOR_APPROVAL,
	STATE_BASELINE_ACCEPTED,
	STATE_BASELINE_REJECTED,
]
WORKFLOW_ACTIONS = [ACTION_SUBMIT, ACTION_APPROVE, ACTION_REJECT, ACTION_REVIEW]


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
	for workflow_name in frappe.get_all(
		"Workflow", filters={"document_type": TARGET_DOCTYPE}, pluck="name"
	):
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

	workflow.append("states", {"state": STATE_DRAFT, "doc_status": "0", "allow_edit": ROLE_WORKFLOW_OWNER})
	workflow.append(
		"states",
		{
			"state": STATE_SUBMITTED_FOR_SPONSOR_APPROVAL,
			"doc_status": "0",
			"allow_edit": ROLE_EXECUTIVE_SPONSOR,
		},
	)
	workflow.append(
		"states",
		{"state": STATE_BASELINE_ACCEPTED, "doc_status": "0", "allow_edit": ROLE_SYSTEM_MANAGER},
	)
	workflow.append(
		"states",
		{"state": STATE_BASELINE_REJECTED, "doc_status": "0", "allow_edit": ROLE_WORKFLOW_OWNER},
	)

	workflow.append(
		"transitions",
		{
			"state": STATE_DRAFT,
			"action": ACTION_SUBMIT,
			"next_state": STATE_SUBMITTED_FOR_SPONSOR_APPROVAL,
			"allowed": ROLE_WORKFLOW_OWNER,
			"allow_self_approval": 1,
		},
	)
	workflow.append(
		"transitions",
		{
			"state": STATE_SUBMITTED_FOR_SPONSOR_APPROVAL,
			"action": ACTION_APPROVE,
			"next_state": STATE_BASELINE_ACCEPTED,
			"allowed": ROLE_EXECUTIVE_SPONSOR,
			"allow_self_approval": 1,
			"condition": "doc.executive_sponsor == frappe.session.user",
		},
	)
	workflow.append(
		"transitions",
		{
			"state": STATE_SUBMITTED_FOR_SPONSOR_APPROVAL,
			"action": ACTION_REJECT,
			"next_state": STATE_BASELINE_REJECTED,
			"allowed": ROLE_EXECUTIVE_SPONSOR,
			"allow_self_approval": 1,
			"condition": "doc.executive_sponsor == frappe.session.user and doc.sponsor_decision_note",
		},
	)
	workflow.append(
		"transitions",
		{
			"state": STATE_BASELINE_REJECTED,
			"action": ACTION_REVIEW,
			"next_state": STATE_DRAFT,
			"allowed": ROLE_WORKFLOW_OWNER,
			"allow_self_approval": 1,
		},
	)

	workflow.insert(ignore_permissions=True)
