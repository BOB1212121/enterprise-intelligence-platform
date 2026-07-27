import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

REQUIRED_KPI_CODES = {"DRR", "DCT", "AER", "OCR", "RER"}
PERCENT_KPI_CODES = {"DRR", "AER", "OCR", "RER"}


class LighthouseWorkflowCharter(Document):
	def validate(self):
		self.validate_accepted_record_immutability()
		self.validate_baseline_date_range()
		self.validate_kpi_rows()
		self.validate_sponsor_state_transition()
		self.set_acceptance_metadata()

	def validate_accepted_record_immutability(self):
		previous = self.get_doc_before_save()
		if not previous:
			return

		if previous.approval_state == "Baseline Accepted" and "System Manager" not in frappe.get_roles():
			frappe.throw("Baseline Accepted records are immutable for non-System Managers.")

	def validate_baseline_date_range(self):
		if self.baseline_start_date and self.baseline_end_date and self.baseline_start_date > self.baseline_end_date:
			frappe.throw("Baseline Start Date cannot be after Baseline End Date.")

	def validate_kpi_rows(self):
		if not self.baseline_kpis:
			frappe.throw("Baseline KPIs are required.")

		seen_codes = []
		for row in self.baseline_kpis:
			kpi_code = (row.kpi_code or "").strip()
			if not kpi_code:
				frappe.throw("Each KPI row must include a KPI Code.")

			seen_codes.append(kpi_code)

			if row.baseline_value is None:
				frappe.throw(f"Baseline Value is required for KPI {kpi_code}.")

			if row.baseline_value < 0:
				frappe.throw(f"Baseline Value cannot be negative for KPI {kpi_code}.")

			if kpi_code in PERCENT_KPI_CODES and not 0 <= row.baseline_value <= 100:
				frappe.throw(f"Percent KPI {kpi_code} must be between 0 and 100.")

		seen_set = set(seen_codes)
		if len(seen_codes) != len(seen_set):
			frappe.throw("Duplicate KPI Code rows are not allowed.")

		if seen_set != REQUIRED_KPI_CODES:
			missing = sorted(REQUIRED_KPI_CODES - seen_set)
			extra = sorted(seen_set - REQUIRED_KPI_CODES)
			parts = []
			if missing:
				parts.append(f"missing: {', '.join(missing)}")
			if extra:
				parts.append(f"unexpected: {', '.join(extra)}")
			details = "; ".join(parts)
			frappe.throw(f"Baseline KPI set must contain exactly DRR, DCT, AER, OCR, RER ({details}).")

	def validate_sponsor_state_transition(self):
		if self.approval_state == "Baseline Rejected" and not self.sponsor_decision_note:
			frappe.throw("Sponsor Decision Note is required when baseline is rejected.")

		previous = self.get_doc_before_save()
		previous_state = previous.approval_state if previous else None
		state_changed = self.approval_state != previous_state
		is_sponsor_state = self.approval_state in {"Baseline Accepted", "Baseline Rejected"}

		if state_changed and is_sponsor_state:
			if frappe.session.user != self.executive_sponsor and "System Manager" not in frappe.get_roles():
				frappe.throw("Only the designated Executive Sponsor can approve or reject this charter.")

	def set_acceptance_metadata(self):
		previous = self.get_doc_before_save()
		previous_state = previous.approval_state if previous else None
		state_changed_to_accepted = self.approval_state == "Baseline Accepted" and previous_state != "Baseline Accepted"

		if state_changed_to_accepted:
			self.baseline_accepted_by = frappe.session.user
			self.baseline_accepted_on = now_datetime()
