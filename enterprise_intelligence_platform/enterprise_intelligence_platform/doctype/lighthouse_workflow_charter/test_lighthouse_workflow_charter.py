import inspect

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import random_string

from enterprise_intelligence_platform.patches.post_model_sync.create_s1_f1_workflow_and_roles import (
	execute as setup_s1_f1,
)


class TestLighthouseWorkflowCharter(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		setup_s1_f1()

		cls.owner_user = cls.make_user_with_role("eip_owner@example.com", "EIP Workflow Owner")
		cls.sponsor_user = cls.make_user_with_role("eip_sponsor@example.com", "EIP Executive Sponsor")
		cls.other_sponsor_user = cls.make_user_with_role(
			"eip_other_sponsor@example.com", "EIP Executive Sponsor"
		)

	def tearDown(self):
		frappe.set_user("Administrator")

	@staticmethod
	def make_user_with_role(email: str, role: str) -> str:
		if not frappe.db.exists("User", email):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": email.split("@")[0],
					"enabled": 1,
					"new_password": random_string(12),
					"send_welcome_email": 0,
				}
			).insert(ignore_permissions=True)

		user = frappe.get_doc("User", email)
		user.add_roles(role)
		return email

	def make_charter_doc(self):
		return frappe.get_doc(
			{
				"doctype": "Lighthouse Workflow Charter",
				"workflow_name": f"Lighthouse {random_string(8)}",
				"business_objective": "Establish baseline accountability charter",
				"in_scope_definition": "One cross-functional commitment workflow",
				"accountable_owner": self.owner_user,
				"executive_sponsor": self.sponsor_user,
				"operating_cadence": "Weekly",
				"baseline_start_date": "2026-07-01",
				"baseline_end_date": "2026-07-20",
				"baseline_kpis": [
					{"kpi_code": "DRR", "baseline_value": 25, "data_source": "Manual Baseline"},
					{"kpi_code": "DCT", "baseline_value": 14, "data_source": "Manual Baseline"},
					{"kpi_code": "AER", "baseline_value": 80, "data_source": "Manual Baseline"},
					{"kpi_code": "OCR", "baseline_value": 90, "data_source": "Manual Baseline"},
					{"kpi_code": "RER", "baseline_value": 22, "data_source": "Manual Baseline"},
				],
			}
		)

	def test_create_valid_charter(self):
		doc = self.make_charter_doc().insert(ignore_permissions=True)
		self.assertEqual(doc.doctype, "Lighthouse Workflow Charter")
		self.assertEqual(len(doc.baseline_kpis), 5)

	def test_invalid_date_range_fails(self):
		doc = self.make_charter_doc()
		doc.baseline_start_date = "2026-07-21"
		doc.baseline_end_date = "2026-07-20"
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_missing_required_kpi_fails(self):
		doc = self.make_charter_doc()
		doc.baseline_kpis = doc.baseline_kpis[:-1]
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_duplicate_kpi_code_fails(self):
		doc = self.make_charter_doc()
		doc.baseline_kpis[1].kpi_code = "DRR"
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_percent_kpi_out_of_range_fails(self):
		doc = self.make_charter_doc()
		doc.baseline_kpis[0].baseline_value = 150
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_only_designated_sponsor_can_approve(self):
		doc = self.make_charter_doc().insert(ignore_permissions=True)
		doc.approval_state = "Submitted for Sponsor Approval"
		doc.save(ignore_permissions=True)

		frappe.set_user(self.other_sponsor_user)
		doc.approval_state = "Baseline Accepted"
		self.assertRaises(frappe.ValidationError, doc.save, ignore_permissions=True)

		frappe.set_user(self.sponsor_user)
		doc.reload()
		doc.approval_state = "Baseline Accepted"
		approved = doc.save(ignore_permissions=True)
		self.assertEqual(approved.approval_state, "Baseline Accepted")
		self.assertEqual(approved.baseline_accepted_by, self.sponsor_user)
		self.assertIsNotNone(approved.baseline_accepted_on)

	def test_reject_requires_decision_note(self):
		doc = self.make_charter_doc().insert(ignore_permissions=True)
		doc.approval_state = "Submitted for Sponsor Approval"
		doc.save(ignore_permissions=True)

		frappe.set_user(self.sponsor_user)
		doc.approval_state = "Baseline Rejected"
		self.assertRaises(frappe.ValidationError, doc.save, ignore_permissions=True)

	def test_accepted_record_immutable_for_non_system_manager(self):
		doc = self.make_charter_doc().insert(ignore_permissions=True)
		doc.approval_state = "Submitted for Sponsor Approval"
		doc.save(ignore_permissions=True)

		frappe.set_user(self.sponsor_user)
		doc.approval_state = "Baseline Accepted"
		doc.save(ignore_permissions=True)

		frappe.set_user(self.owner_user)
		doc.reload()
		doc.business_objective = "Unauthorized mutation"
		self.assertRaises(frappe.ValidationError, doc.save, ignore_permissions=True)

	def test_native_workflow_submit_transition_when_environment_allows(self):
		import frappe.model.workflow as workflow_module

		func = workflow_module.apply_workflow
		while hasattr(func, "__wrapped__"):
			func = func.__wrapped__

		source_file = inspect.getsourcefile(func) or ""
		if not source_file.endswith("/apps/frappe/frappe/model/workflow.py"):
			self.skipTest(
				"Workflow apply function is overridden by another app in this environment; skipping native workflow regression test."
			)

		doc = self.make_charter_doc().insert(ignore_permissions=True)
		frappe.set_user(self.owner_user)
		transitioned = workflow_module.apply_workflow(doc, "Submit")
		self.assertEqual(transitioned.approval_state, "Submitted for Sponsor Approval")
