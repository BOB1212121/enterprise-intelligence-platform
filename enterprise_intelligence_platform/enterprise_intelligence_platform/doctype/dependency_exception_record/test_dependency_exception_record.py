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
from enterprise_intelligence_platform.patches.post_model_sync.create_s1_f3_workflow_and_roles import (
	execute as setup_s1_f3,
)


class TestDependencyExceptionRecord(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		setup_s1_f1()
		setup_s1_f2()
		setup_s1_f3()

		cls.owner_user = cls.make_user_with_role("eip_dependency_owner@example.com", "EIP Workflow Owner")
		cls.sponsor_user = cls.make_user_with_role(
			"eip_dependency_sponsor@example.com", "EIP Executive Sponsor"
		)
		cls.other_sponsor_user = cls.make_user_with_role(
			"eip_dependency_other_sponsor@example.com", "EIP Executive Sponsor"
		)
		cls.operations_user = cls.make_user_with_role(
			"eip_dependency_operations@example.com", "EIP Operations Manager"
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
				"workflow_name": f"S1F3 Charter {random_string(8)}",
				"business_objective": "Enable cross-functional dependency governance",
				"in_scope_definition": "Decision-linked dependency control",
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
				"decision_title": f"S1F3 Decision {random_string(8)}",
				"lighthouse_workflow_charter": charter.name,
				"accountable_owner": self.owner_user,
				"executive_sponsor": self.sponsor_user,
				"decision_type": "Operational",
				"decision_criticality": "Medium",
				"proposal_date": "2026-07-15",
				"target_decision_date": "2026-07-20",
				"business_decision_summary": "Choose integration release sequence.",
				"tradeoff_summary": "Speed versus rollback risk.",
				"assumptions": [
					{
						"assumption_text": "Vendor dependency remains stable.",
						"confidence_score": 0.8,
						"falsifiability_note": "Invalidate if SLA misses twice.",
					}
				],
			}
		).insert(ignore_permissions=True)

	def make_dependency_doc(self):
		decision = self.make_decision_doc()
		return frappe.get_doc(
			{
				"doctype": "Dependency Exception Record",
				"dependency_title": f"Dependency {random_string(8)}",
				"decision_record": decision.name,
				"lighthouse_workflow_charter": decision.lighthouse_workflow_charter,
				"accountable_owner": self.owner_user,
				"executive_sponsor": self.sponsor_user,
				"dependency_type": "System",
				"dependency_criticality": "High",
				"declaration_date": "2026-07-18",
				"target_resolution_date": "2026-07-25",
				"dependency_status": "Open",
				"dependency_description": "ERP payment gateway schema update is pending.",
				"impact_summary": "Go-live blocked if schema is not delivered.",
				"mitigation_plan": "Introduce phased cutover and rollback checkpoints.",
				"exception_required": 1,
				"exception_owner": self.owner_user,
				"exception_reason": "Need temporary override for release window.",
				"exception_expiry_date": "2026-07-30",
				"remediation_intent": "Remove override after gateway schema lands.",
			}
		)

	def test_create_valid_dependency_exception_record(self):
		doc = self.make_dependency_doc().insert(ignore_permissions=True)
		self.assertEqual(doc.doctype, "Dependency Exception Record")
		self.assertEqual(doc.dependency_status, "Open")

	def test_target_resolution_date_cannot_precede_declaration_date(self):
		doc = self.make_dependency_doc()
		doc.target_resolution_date = "2026-07-17"
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_exception_fields_required_when_exception_enabled(self):
		doc = self.make_dependency_doc()
		doc.exception_reason = ""
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_exception_expiry_cannot_precede_declaration_date(self):
		doc = self.make_dependency_doc()
		doc.exception_expiry_date = "2026-07-17"
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_resolved_status_requires_resolution_note(self):
		doc = self.make_dependency_doc()
		doc.dependency_status = "Resolved"
		doc.resolution_note = ""
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_sponsor_must_match_linked_decision_record(self):
		doc = self.make_dependency_doc()
		doc.executive_sponsor = self.other_sponsor_user
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_only_designated_sponsor_can_approve(self):
		doc = self.make_dependency_doc().insert(ignore_permissions=True)
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

	def test_reject_requires_sponsor_decision_note(self):
		doc = self.make_dependency_doc().insert(ignore_permissions=True)
		doc.approval_state = "Submitted for Approval"
		doc.save(ignore_permissions=True)

		frappe.set_user(self.sponsor_user)
		doc.approval_state = "Rejected"
		self.assertRaises(frappe.ValidationError, doc.save, ignore_permissions=True)

	def test_approved_record_immutable_for_non_system_manager(self):
		doc = self.make_dependency_doc().insert(ignore_permissions=True)
		doc.approval_state = "Submitted for Approval"
		doc.save(ignore_permissions=True)

		frappe.set_user(self.sponsor_user)
		doc.approval_state = "Approved"
		doc.save(ignore_permissions=True)

		frappe.set_user(self.owner_user)
		doc.reload()
		doc.impact_summary = "Unauthorized mutation"
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

		doc = self.make_dependency_doc().insert(ignore_permissions=True)
		frappe.set_user(self.owner_user)
		transitioned = workflow_module.apply_workflow(doc, "Submit")
		self.assertEqual(transitioned.approval_state, "Submitted for Approval")

	def test_illegal_direct_transition_draft_to_approved_is_blocked(self):
		doc = self.make_dependency_doc().insert(ignore_permissions=True)
		frappe.set_user(self.sponsor_user)
		doc.approval_state = "Approved"
		self.assertRaises(frappe.ValidationError, doc.save, ignore_permissions=True)

	def test_insert_with_draft_succeeds(self):
		doc = self.make_dependency_doc()
		doc.approval_state = "Draft"
		inserted = doc.insert(ignore_permissions=True)
		self.assertEqual(inserted.approval_state, "Draft")

	def test_insert_with_submitted_fails(self):
		doc = self.make_dependency_doc()
		doc.approval_state = "Submitted for Approval"
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_insert_with_approved_fails(self):
		doc = self.make_dependency_doc()
		doc.approval_state = "Approved"
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_insert_with_rejected_fails(self):
		doc = self.make_dependency_doc()
		doc.approval_state = "Rejected"
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_owner_can_create_without_permission_bypass(self):
		frappe.set_user(self.owner_user)
		doc = self.make_dependency_doc().insert()
		self.assertEqual(doc.doctype, "Dependency Exception Record")

	def test_sponsor_cannot_create_without_permission_bypass(self):
		frappe.set_user(self.sponsor_user)
		doc = self.make_dependency_doc()
		self.assertRaises(frappe.PermissionError, doc.insert)

	def test_operations_manager_cannot_write_without_permission_bypass(self):
		frappe.set_user("Administrator")
		doc = self.make_dependency_doc().insert()
		frappe.set_user(self.operations_user)
		doc.reload()
		doc.impact_summary = "Ops manager edit attempt"
		self.assertRaises(frappe.PermissionError, doc.save)

	def test_empty_approval_state_is_normalized_to_draft(self):
		# Existing doc via save() (normal path)
		doc_save = self.make_dependency_doc().insert(ignore_permissions=True)
		doc_save.reload()
		doc_save.approval_state = ""
		doc_save.save()
		doc_save.reload()
		self.assertEqual(doc_save.approval_state, "Draft")

		# Existing doc via save(ignore_permissions=True)
		doc_save_ignore = self.make_dependency_doc().insert(ignore_permissions=True)
		doc_save_ignore.reload()
		doc_save_ignore.approval_state = ""
		doc_save_ignore.save(ignore_permissions=True)
		doc_save_ignore.reload()
		self.assertEqual(doc_save_ignore.approval_state, "Draft")

		# New doc via insert(ignore_permissions=True)
		doc_insert = self.make_dependency_doc()
		doc_insert.approval_state = ""
		doc_insert.insert(ignore_permissions=True)
		doc_insert.reload()
		self.assertEqual(doc_insert.approval_state, "Draft")
