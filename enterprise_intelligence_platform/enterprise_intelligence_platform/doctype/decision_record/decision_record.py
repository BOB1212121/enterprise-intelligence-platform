import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

STATE_APPROVED = "Approved"
STATE_REJECTED = "Rejected"
ROLE_SYSTEM_MANAGER = "System Manager"
SCORE_MIN = 0
SCORE_MAX = 1


class DecisionRecord(Document):
	def validate(self):
		self.validate_approved_record_immutability()
		self.validate_charter_linkage()
		self.validate_dates()
		self.validate_assumptions()
		self.validate_sponsor_state_transition()
		self.set_approval_metadata()

	def validate_approved_record_immutability(self):
		previous = self.get_doc_before_save()
		if not previous:
			return

		if previous.approval_state == STATE_APPROVED and ROLE_SYSTEM_MANAGER not in frappe.get_roles():
			frappe.throw(_("Approved Decision Records are immutable for non-System Managers."))

	def validate_charter_linkage(self):
		if not self.lighthouse_workflow_charter:
			frappe.throw(_("Lighthouse Workflow Charter is required."))

		charter_sponsor = frappe.db.get_value(
			"Lighthouse Workflow Charter", self.lighthouse_workflow_charter, "executive_sponsor"
		)
		if not charter_sponsor:
			frappe.throw(_("Linked Lighthouse Workflow Charter could not be resolved."))

		if not self.executive_sponsor:
			self.executive_sponsor = charter_sponsor

		if self.executive_sponsor != charter_sponsor:
			frappe.throw(_("Executive Sponsor must match the linked Lighthouse Workflow Charter."))

	def validate_dates(self):
		if self.proposal_date and self.target_decision_date and self.target_decision_date < self.proposal_date:
			frappe.throw(_("Target Decision Date cannot be before Proposal Date."))

	def validate_assumptions(self):
		if not self.assumptions:
			frappe.throw(_("At least one assumption is required."))

		seen_assumptions = set()
		for row in self.assumptions:
			assumption_text = (row.assumption_text or "").strip()
			if not assumption_text:
				frappe.throw(_("Each assumption row must include Assumption text."))

			normalized = assumption_text.casefold()
			if normalized in seen_assumptions:
				frappe.throw(_("Duplicate assumptions are not allowed."))
			seen_assumptions.add(normalized)

			if row.confidence_score is None:
				frappe.throw(_("Confidence Score is required for each assumption."))

			if not SCORE_MIN <= row.confidence_score <= SCORE_MAX:
				frappe.throw(
					_("Confidence Score must be between {min_score} and {max_score}.").format(
						min_score=SCORE_MIN, max_score=SCORE_MAX
					)
				)

	def validate_sponsor_state_transition(self):
		if self.approval_state == STATE_REJECTED and not self.decision_note:
			frappe.throw(_("Decision Note is required when a decision is rejected."))

		previous = self.get_doc_before_save()
		previous_state = previous.approval_state if previous else None
		state_changed = self.approval_state != previous_state
		is_sponsor_state = self.approval_state in {STATE_APPROVED, STATE_REJECTED}

		if state_changed and is_sponsor_state:
			if frappe.session.user != self.executive_sponsor and ROLE_SYSTEM_MANAGER not in frappe.get_roles():
				frappe.throw(_("Only the designated Executive Sponsor can approve or reject this decision."))

	def set_approval_metadata(self):
		previous = self.get_doc_before_save()
		previous_state = previous.approval_state if previous else None
		state_changed_to_approved = self.approval_state == STATE_APPROVED and previous_state != STATE_APPROVED

		if state_changed_to_approved:
			self.approved_by = frappe.session.user
			self.approved_on = now_datetime()
