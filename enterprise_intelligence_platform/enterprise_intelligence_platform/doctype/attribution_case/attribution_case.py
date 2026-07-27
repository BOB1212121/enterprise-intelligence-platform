import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

STATE_DRAFT = "Draft"
STATE_SUBMITTED_FOR_APPROVAL = "Submitted for Approval"
STATE_APPROVED = "Approved"
STATE_REJECTED = "Rejected"
ROLE_SYSTEM_MANAGER = "System Manager"
SCORE_MIN = 0
SCORE_MAX = 1
ALLOWED_STATE_TRANSITIONS = {
	(STATE_DRAFT, STATE_SUBMITTED_FOR_APPROVAL),
	(STATE_SUBMITTED_FOR_APPROVAL, STATE_APPROVED),
	(STATE_SUBMITTED_FOR_APPROVAL, STATE_REJECTED),
	(STATE_REJECTED, STATE_DRAFT),
}


class AttributionCase(Document):
	def validate(self):
		previous = self.get_doc_before_save()
		roles = set(frappe.get_roles())

		self.validate_state_transition(previous)
		self.validate_approved_record_immutability(previous, roles)
		self.validate_decision_linkage()
		self.validate_observation_dates()
		self.validate_confidence()
		self.validate_chain_steps()
		self.validate_evidence_rows()
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
			frappe.throw(_("Approved attribution cases are immutable for non-System Managers."))

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

	def validate_observation_dates(self):
		if (
			self.observation_start_date
			and self.observation_end_date
			and self.observation_end_date < self.observation_start_date
		):
			frappe.throw(_("Observation End Date cannot be before Observation Start Date."))

	def validate_confidence(self):
		if self.confidence_score is None:
			frappe.throw(_("Confidence Score is required."))

		if not SCORE_MIN <= self.confidence_score <= SCORE_MAX:
			frappe.throw(
				_("Confidence Score must be between {min_score} and {max_score}.").format(
					min_score=SCORE_MIN, max_score=SCORE_MAX
				)
			)

		if not self.confidence_rationale:
			frappe.throw(_("Confidence Rationale is required."))

	def validate_chain_steps(self):
		if not self.attribution_chain_steps:
			frappe.throw(_("At least one Attribution Chain Step is required."))

		seen_sequences = set()
		for row in self.attribution_chain_steps:
			if row.sequence_no is None or row.sequence_no <= 0:
				frappe.throw(_("Attribution Chain Step Sequence No must be greater than zero."))

			if row.sequence_no in seen_sequences:
				frappe.throw(_("Duplicate Attribution Chain Step Sequence No values are not allowed."))
			seen_sequences.add(row.sequence_no)

			if not row.step_summary:
				frappe.throw(_("Each Attribution Chain Step requires Step Summary."))

			if row.dependency_exception_record:
				dependency_decision = frappe.db.get_value(
					"Dependency Exception Record", row.dependency_exception_record, "decision_record"
				)
				if not dependency_decision:
					frappe.throw(_("Linked Dependency Exception Record could not be resolved."))

				if dependency_decision != self.decision_record:
					frappe.throw(
						_("Linked Dependency Exception Record must belong to the same Decision Record.")
					)

	def validate_evidence_rows(self):
		if not self.attribution_evidence:
			frappe.throw(_("At least one Attribution Evidence row is required."))

		for row in self.attribution_evidence:
			if not row.evidence_type:
				frappe.throw(_("Evidence Type is required for each Attribution Evidence row."))

			normalized_supports_claim = self._normalize_checkbox_value(row.supports_claim, "Supports Claim")
			row.supports_claim = normalized_supports_claim
			if normalized_supports_claim not in (0, 1):
				frappe.throw(_("Supports Claim must be either 0 or 1."))

			if not row.evidence_reference:
				frappe.throw(_("Evidence Reference is required for each Attribution Evidence row."))

	@staticmethod
	def _normalize_checkbox_value(value, field_label):
		if isinstance(value, bool):
			return 1 if value else 0

		if isinstance(value, int):
			if value in (0, 1):
				return value
			frappe.throw(_("{field_label} must be either 0 or 1.").format(field_label=field_label))

		if isinstance(value, str):
			normalized = value.strip().lower()
			if normalized in {"0", "false"}:
				return 0
			if normalized in {"1", "true"}:
				return 1

		frappe.throw(_("{field_label} must be either 0 or 1.").format(field_label=field_label))

	def validate_sponsor_state_transition(self, previous, roles):
		if self.approval_state == STATE_REJECTED and not self.sponsor_decision_note:
			frappe.throw(_("Sponsor Decision Note is required when an attribution case is rejected."))

		previous_state = previous.approval_state if previous else None
		state_changed = self.approval_state != previous_state
		is_sponsor_state = self.approval_state in {STATE_APPROVED, STATE_REJECTED}

		if state_changed and is_sponsor_state:
			if frappe.session.user != self.executive_sponsor and ROLE_SYSTEM_MANAGER not in roles:
				frappe.throw(_("Only the designated Executive Sponsor can approve or reject this case."))

	def set_approval_metadata(self, previous):
		previous_state = previous.approval_state if previous else None
		state_changed_to_approved = self.approval_state == STATE_APPROVED and previous_state != STATE_APPROVED

		if state_changed_to_approved:
			self.approved_by = frappe.session.user
			self.approved_on = now_datetime()
