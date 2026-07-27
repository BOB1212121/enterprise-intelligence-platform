import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, now_datetime

STATE_DRAFT = "Draft"
STATE_SUBMITTED_FOR_APPROVAL = "Submitted for Approval"
STATE_APPROVED = "Approved"
STATE_REJECTED = "Rejected"
STATUS_RESOLVED = "Resolved"
ROLE_SYSTEM_MANAGER = "System Manager"
ALLOWED_STATE_TRANSITIONS = {
	(STATE_DRAFT, STATE_SUBMITTED_FOR_APPROVAL),
	(STATE_SUBMITTED_FOR_APPROVAL, STATE_APPROVED),
	(STATE_SUBMITTED_FOR_APPROVAL, STATE_REJECTED),
	(STATE_REJECTED, STATE_DRAFT),
}


class DependencyExceptionRecord(Document):
	def validate(self):
		previous = self.get_doc_before_save()
		roles = set(frappe.get_roles())

		self.validate_state_transition(previous)
		self.validate_approved_record_immutability(previous, roles)
		self.validate_decision_linkage()
		self.validate_dates()
		self.validate_dependency_status_rules()
		self.validate_exception_rules()
		self.validate_sponsor_state_transition(previous, roles)
		self.set_approval_metadata(previous)

	def validate_state_transition(self, previous):
		if not previous:
			if not self.approval_state:
				self.approval_state = STATE_DRAFT

			if self.approval_state != STATE_DRAFT:
				frappe.throw(
					_("Illegal initial approval state on insert: {to_state}. Must be {initial_state}.").format(
						to_state=self.approval_state,
						initial_state=STATE_DRAFT,
					)
				)
			return

		previous_state = previous.approval_state or ""
		current_state = self.approval_state or previous_state

		if current_state == previous_state:
			return

		if (previous_state, current_state) not in ALLOWED_STATE_TRANSITIONS:
			frappe.throw(_("Illegal approval state transition from {from_state} to {to_state}.").format(
				from_state=previous_state or _("(empty)"), to_state=current_state or _("(empty)")
			))

	def validate_approved_record_immutability(self, previous, roles):
		if not previous:
			return

		if previous.approval_state == STATE_APPROVED and ROLE_SYSTEM_MANAGER not in roles:
			frappe.throw(_("Approved dependency records are immutable for non-System Managers."))

	def validate_decision_linkage(self):
		if not self.decision_record:
			frappe.throw(_("Decision Record is required."))

		decision_values = frappe.db.get_value(
			"Decision Record",
			self.decision_record,
			["executive_sponsor", "lighthouse_workflow_charter"],
			as_dict=True,
		)
		if not decision_values:
			frappe.throw(_("Linked Decision Record could not be resolved."))

		decision_sponsor = decision_values.executive_sponsor
		decision_charter = decision_values.lighthouse_workflow_charter

		if not decision_sponsor or not decision_charter:
			frappe.throw(_("Linked Decision Record must include Executive Sponsor and Lighthouse Workflow Charter."))

		if not self.executive_sponsor:
			self.executive_sponsor = decision_sponsor

		if not self.lighthouse_workflow_charter:
			self.lighthouse_workflow_charter = decision_charter

		if self.executive_sponsor != decision_sponsor:
			frappe.throw(_("Executive Sponsor must match the linked Decision Record."))

		if self.lighthouse_workflow_charter != decision_charter:
			frappe.throw(_("Lighthouse Workflow Charter must match the linked Decision Record."))

	def validate_dates(self):
		if (
			self.declaration_date
			and self.target_resolution_date
			and self.target_resolution_date < self.declaration_date
		):
			frappe.throw(_("Target Resolution Date cannot be before Declaration Date."))

		if (
			self.exception_expiry_date
			and self.declaration_date
			and self.exception_expiry_date < self.declaration_date
		):
			frappe.throw(_("Exception Expiry Date cannot be before Declaration Date."))

	def validate_dependency_status_rules(self):
		if self.dependency_status == STATUS_RESOLVED and not self.resolution_note:
			frappe.throw(_("Resolution Note is required when dependency status is Resolved."))

	def validate_exception_rules(self):
		if not cint(self.exception_required):
			self.exception_owner = None
			self.exception_reason = None
			self.exception_expiry_date = None
			self.remediation_intent = None
			return

		if not self.exception_owner:
			frappe.throw(_("Exception Owner is required when Exception Required is enabled."))

		if not self.exception_reason:
			frappe.throw(_("Exception Reason is required when Exception Required is enabled."))

		if not self.exception_expiry_date:
			frappe.throw(_("Exception Expiry Date is required when Exception Required is enabled."))

		if not self.remediation_intent:
			frappe.throw(_("Remediation Intent is required when Exception Required is enabled."))

	def validate_sponsor_state_transition(self, previous, roles):
		if self.approval_state == STATE_REJECTED and not self.sponsor_decision_note:
			frappe.throw(_("Sponsor Decision Note is required when a dependency record is rejected."))

		previous_state = previous.approval_state if previous else None
		state_changed = self.approval_state != previous_state
		is_sponsor_state = self.approval_state in {STATE_APPROVED, STATE_REJECTED}

		if state_changed and is_sponsor_state:
			if frappe.session.user != self.executive_sponsor and ROLE_SYSTEM_MANAGER not in roles:
				frappe.throw(_("Only the designated Executive Sponsor can approve or reject this record."))

	def set_approval_metadata(self, previous):
		previous_state = previous.approval_state if previous else None
		state_changed_to_approved = self.approval_state == STATE_APPROVED and previous_state != STATE_APPROVED

		if state_changed_to_approved:
			self.approved_by = frappe.session.user
			self.approved_on = now_datetime()
