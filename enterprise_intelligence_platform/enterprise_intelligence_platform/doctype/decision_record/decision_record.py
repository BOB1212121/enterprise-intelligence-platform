import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


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

		if previous.approval_state == "Approved" and "System Manager" not in frappe.get_roles():
			frappe.throw("Approved Decision Records are immutable for non-System Managers.")

	def validate_charter_linkage(self):
		if not self.lighthouse_workflow_charter:
			frappe.throw("Lighthouse Workflow Charter is required.")

		charter = frappe.get_doc("Lighthouse Workflow Charter", self.lighthouse_workflow_charter)
		charter_sponsor = charter.executive_sponsor
		if not self.executive_sponsor:
			self.executive_sponsor = charter_sponsor

		if self.executive_sponsor != charter_sponsor:
			frappe.throw("Executive Sponsor must match the linked Lighthouse Workflow Charter.")

	def validate_dates(self):
		if self.proposal_date and self.target_decision_date and self.target_decision_date < self.proposal_date:
			frappe.throw("Target Decision Date cannot be before Proposal Date.")

	def validate_assumptions(self):
		if not self.assumptions:
			frappe.throw("At least one assumption is required.")

		seen_assumptions = set()
		for row in self.assumptions:
			assumption_text = (row.assumption_text or "").strip()
			if not assumption_text:
				frappe.throw("Each assumption row must include Assumption text.")

			normalized = assumption_text.casefold()
			if normalized in seen_assumptions:
				frappe.throw("Duplicate assumptions are not allowed.")
			seen_assumptions.add(normalized)

			if row.confidence_score is None:
				frappe.throw("Confidence Score is required for each assumption.")

			if not 0 <= row.confidence_score <= 1:
				frappe.throw("Confidence Score must be between 0 and 1.")

	def validate_sponsor_state_transition(self):
		if self.approval_state == "Rejected" and not self.decision_note:
			frappe.throw("Decision Note is required when a decision is rejected.")

		previous = self.get_doc_before_save()
		previous_state = previous.approval_state if previous else None
		state_changed = self.approval_state != previous_state
		is_sponsor_state = self.approval_state in {"Approved", "Rejected"}

		if state_changed and is_sponsor_state:
			if frappe.session.user != self.executive_sponsor and "System Manager" not in frappe.get_roles():
				frappe.throw("Only the designated Executive Sponsor can approve or reject this decision.")

	def set_approval_metadata(self):
		previous = self.get_doc_before_save()
		previous_state = previous.approval_state if previous else None
		state_changed_to_approved = self.approval_state == "Approved" and previous_state != "Approved"

		if state_changed_to_approved:
			self.approved_by = frappe.session.user
			self.approved_on = now_datetime()
