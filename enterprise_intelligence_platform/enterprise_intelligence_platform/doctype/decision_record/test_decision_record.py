import inspect

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import random_string

from enterprise_intelligence_platform.patches.post_model_sync.create_s1_f1_workflow_and_roles import (
	execute as setup_s1_f1,
)
from enterprise_intelligence_platform.patches.post_model_sync.create_s1_f2_workflow_and_roles import (
	execute as setup_s1_f2,
)


class TestDecisionRecord(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		setup_s1_f1()
		setup_s1_f2()

		cls.owner_user = cls.make_user_with_role("eip_decision_owner@example.com", "EIP Workflow Owner")
		cls.sponsor_user = cls.make_user_with_role(
			"eip_decision_sponsor@example.com", "EIP Executive Sponsor"
		)
		cls.other_sponsor_user = cls.make_user_with_role(
			"eip_decision_other_sponsor@example.com", "EIP Executive Sponsor"
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
				"workflow_name": f"S1F2 Charter {random_string(8)}",
				"business_objective": "Enable decision accountability",
				"in_scope_definition": "One workflow",
				"accountable_owner": self.owner_user,
				"executive_sponsor": self.sponsor_user,
				"operating_cadence": "Weekly",
				"baseline_start_date": "2026-07-01",
				"baseline_end_date": "2026-07-20",
				"baseline_kpis": [
					{"kpi_code": "DRR", "baseline_value": 25, "data_source": "Baseline"},
					{"kpi_code": "DCT", "baseline_value": 14, "data_source": "Baseline"},
					{"kpi_code": "AER", "baseline_value": 80, "data_source": "Baseline"},
					{"kpi_code": "OCR", "baseline_value": 90, "data_source": "Baseline"},
					{"kpi_code": "RER", "baseline_value": 22, "data_source": "Baseline"},
				],
			}
		).insert(ignore_permissions=True)

	def make_decision_doc(self):
		charter = self.make_charter_doc()
		return frappe.get_doc(
			{
				"doctype": "Decision Record",
				"decision_title": f"Decision {random_string(8)}",
				"lighthouse_workflow_charter": charter.name,
				"accountable_owner": self.owner_user,
				"executive_sponsor": self.sponsor_user,
				"decision_type": "Operational",
				"decision_criticality": "Medium",
				"proposal_date": "2026-07-15",
				"target_decision_date": "2026-07-20",
				"business_decision_summary": "Choose fulfillment policy.",
				"tradeoff_summary": "Speed versus margin stability.",
				"assumptions": [
					{
						"assumption_text": "Demand trend remains stable.",
						"confidence_score": 0.8,
						"falsifiability_note": "Invalidate if weekly variance >20%.",
					}
				],
			}
		)

	def test_create_valid_decision_record(self):
		doc = self.make_decision_doc().insert(ignore_permissions=True)
		self.assertEqual(doc.doctype, "Decision Record")
		self.assertEqual(len(doc.assumptions), 1)

	def test_requires_at_least_one_assumption(self):
		doc = self.make_decision_doc()
		doc.assumptions = []
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_confidence_score_range_validation(self):
		doc = self.make_decision_doc()
		doc.assumptions[0].confidence_score = 1.2
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_target_date_cannot_precede_proposal_date(self):
		doc = self.make_decision_doc()
		doc.target_decision_date = "2026-07-10"
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_executive_sponsor_must_match_charter(self):
		doc = self.make_decision_doc()
		doc.executive_sponsor = self.other_sponsor_user
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_only_designated_sponsor_can_approve(self):
		doc = self.make_decision_doc().insert(ignore_permissions=True)
		doc.approval_state = "Submitted for Approval"
		doc.save(ignore_permissions=True)

		frappe.set_user(self.other_sponsor_user)
		doc.approval_state = "Approved"
		self.assertRaises(frappe.ValidationError, doc.save, ignore_permissions=True)

		frappe.set_user(self.sponsor_user)
		doc.reload()
		doc.approval_state = "Approved"
		approved = doc.save(ignore_permissions=True)
		self.assertEqual(approved.approval_state, "Approved")
		self.assertEqual(approved.approved_by, self.sponsor_user)
		self.assertIsNotNone(approved.approved_on)

	def test_reject_requires_decision_note(self):
		doc = self.make_decision_doc().insert(ignore_permissions=True)
		doc.approval_state = "Submitted for Approval"
		doc.save(ignore_permissions=True)

		frappe.set_user(self.sponsor_user)
		doc.approval_state = "Rejected"
		self.assertRaises(frappe.ValidationError, doc.save, ignore_permissions=True)

	def test_approved_record_immutable_for_non_system_manager(self):
		doc = self.make_decision_doc().insert(ignore_permissions=True)
		doc.approval_state = "Submitted for Approval"
		doc.save(ignore_permissions=True)

		frappe.set_user(self.sponsor_user)
		doc.approval_state = "Approved"
		doc.save(ignore_permissions=True)

		frappe.set_user(self.owner_user)
		doc.reload()
		doc.business_decision_summary = "Unauthorized update"
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

		doc = self.make_decision_doc().insert(ignore_permissions=True)
		frappe.set_user(self.owner_user)
		transitioned = workflow_module.apply_workflow(doc, "Submit")
		self.assertEqual(transitioned.approval_state, "Submitted for Approval")
