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
from enterprise_intelligence_platform.patches.post_model_sync.create_s2_f2_workflow_and_roles import (
	execute as setup_s2_f2,
)


class TestAttributionCase(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		setup_s1_f1()
		setup_s1_f2()
		setup_s1_f3()
		setup_s2_f2()

		cls.owner_user = cls.make_user_with_role("eip_attribution_owner@example.com", "EIP Workflow Owner")
		cls.sponsor_user = cls.make_user_with_role("eip_attribution_sponsor@example.com", "EIP Executive Sponsor")
		cls.other_sponsor_user = cls.make_user_with_role(
			"eip_attribution_other_sponsor@example.com", "EIP Executive Sponsor"
		)
		cls.operations_user = cls.make_user_with_role(
			"eip_attribution_operations@example.com", "EIP Operations Manager"
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
				"workflow_name": f"S2F2 Charter {random_string(8)}",
				"business_objective": "Establish attribution governance.",
				"in_scope_definition": "Attribution confidence traceability.",
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
				"decision_title": f"S2F2 Decision {random_string(8)}",
				"lighthouse_workflow_charter": charter.name,
				"accountable_owner": self.owner_user,
				"executive_sponsor": self.sponsor_user,
				"decision_type": "Operational",
				"decision_criticality": "Medium",
				"proposal_date": "2026-07-15",
				"target_decision_date": "2026-07-20",
				"business_decision_summary": "Introduce attribution case controls.",
				"tradeoff_summary": "Slightly higher data entry for stronger governance.",
				"assumptions": [
					{
						"assumption_text": "Evidence can be captured per cycle.",
						"confidence_score": 0.8,
						"falsifiability_note": "Fails if cycle capture is incomplete.",
					}
				],
			}
		).insert(ignore_permissions=True)

	def make_dependency_doc(self, decision=None):
		decision = decision or self.make_decision_doc()
		return frappe.get_doc(
			{
				"doctype": "Dependency Exception Record",
				"dependency_title": f"S2F2 Dependency {random_string(8)}",
				"decision_record": decision.name,
				"lighthouse_workflow_charter": decision.lighthouse_workflow_charter,
				"accountable_owner": self.owner_user,
				"executive_sponsor": self.sponsor_user,
				"dependency_type": "System",
				"dependency_criticality": "High",
				"declaration_date": "2026-07-18",
				"target_resolution_date": "2026-07-25",
				"dependency_status": "Open",
				"dependency_description": "Reference dependency for attribution chain.",
				"impact_summary": "Influences attribution confidence.",
				"mitigation_plan": "Mitigate and monitor.",
				"exception_required": 1,
				"exception_owner": self.owner_user,
				"exception_reason": "Temporary exception for controlled rollout.",
				"exception_expiry_date": "2026-07-30",
				"remediation_intent": "Remove exception after rollout stabilizes.",
			}
		).insert(ignore_permissions=True)

	def make_attribution_case_doc(self, decision=None, dependency=None):
		decision = decision or self.make_decision_doc()
		dependency = dependency or self.make_dependency_doc(decision=decision)

		return frappe.get_doc(
			{
				"doctype": "Attribution Case",
				"attribution_title": f"S2F2 Attribution {random_string(8)}",
				"decision_record": decision.name,
				"lighthouse_workflow_charter": decision.lighthouse_workflow_charter,
				"accountable_owner": self.owner_user,
				"executive_sponsor": self.sponsor_user,
				"observation_start_date": "2026-07-20",
				"observation_end_date": "2026-07-25",
				"attribution_summary": "Cycle time improved after decision execution.",
				"confounder_summary": "Minor staffing volatility during the period.",
				"confidence_score": 0.7,
				"confidence_rationale": "Metric and ops review evidence align.",
				"attribution_chain_steps": [
					{
						"sequence_no": 1,
						"step_summary": "Decision implemented in controlled scope.",
						"dependency_exception_record": dependency.name,
					}
				],
				"attribution_evidence": [
					{
						"evidence_type": "Metric",
						"supports_claim": 1,
						"evidence_reference": "KPI dashboard snapshot 2026-07-25",
						"evidence_date": "2026-07-25",
					}
				],
			}
		)

	def make_attribution_case_doc_with_supports_claim(self, supports_claim):
		doc = self.make_attribution_case_doc()
		doc.attribution_evidence[0].supports_claim = supports_claim
		return doc

	def test_create_valid_attribution_case(self):
		doc = self.make_attribution_case_doc().insert(ignore_permissions=True)
		self.assertEqual(doc.doctype, "Attribution Case")
		self.assertEqual(doc.approval_state, "Draft")

	def test_observation_end_date_cannot_precede_start_date(self):
		doc = self.make_attribution_case_doc()
		doc.observation_end_date = "2026-07-19"
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_confidence_score_range_validation(self):
		doc = self.make_attribution_case_doc()
		doc.confidence_score = 1.1
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_confidence_rationale_is_required(self):
		doc = self.make_attribution_case_doc()
		doc.confidence_rationale = ""
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_supports_claim_accepts_common_boolean_representations(self):
		accepted_values = [
			0,
			1,
			"0",
			"1",
			False,
			True,
		]

		for value in accepted_values:
			doc = self.make_attribution_case_doc_with_supports_claim(value)
			inserted = doc.insert(ignore_permissions=True)
			self.assertIn(inserted.attribution_evidence[0].supports_claim, (0, 1))

	def test_supports_claim_rejects_invalid_boolean_representations(self):
		rejected_values = ["yes", "abc", 2, -1]

		for value in rejected_values:
			doc = self.make_attribution_case_doc_with_supports_claim(value)
			self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_supports_claim_rejects_raw_none_value_in_controller_validation(self):
		doc = self.make_attribution_case_doc()
		doc.attribution_evidence[0].supports_claim = None
		self.assertRaises(frappe.ValidationError, doc.validate_evidence_rows)

	def test_requires_at_least_one_chain_step(self):
		doc = self.make_attribution_case_doc()
		doc.attribution_chain_steps = []
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_requires_at_least_one_evidence_row(self):
		doc = self.make_attribution_case_doc()
		doc.attribution_evidence = []
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_duplicate_chain_sequence_is_blocked(self):
		doc = self.make_attribution_case_doc()
		doc.append(
			"attribution_chain_steps",
			{
				"sequence_no": 1,
				"step_summary": "Duplicate sequence should fail.",
			},
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_chain_dependency_must_match_decision(self):
		decision_a = self.make_decision_doc()
		decision_b = self.make_decision_doc()
		dependency_b = self.make_dependency_doc(decision=decision_b)

		doc = self.make_attribution_case_doc(decision=decision_a)
		doc.attribution_chain_steps[0].dependency_exception_record = dependency_b.name
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_sponsor_must_match_linked_decision_record(self):
		doc = self.make_attribution_case_doc()
		doc.executive_sponsor = self.other_sponsor_user
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_charter_must_match_linked_decision_record(self):
		doc = self.make_attribution_case_doc()
		doc.lighthouse_workflow_charter = self.make_charter_doc().name
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_only_designated_sponsor_can_approve(self):
		doc = self.make_attribution_case_doc().insert(ignore_permissions=True)
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
		doc = self.make_attribution_case_doc().insert(ignore_permissions=True)
		doc.approval_state = "Submitted for Approval"
		doc.save(ignore_permissions=True)

		frappe.set_user(self.sponsor_user)
		doc.approval_state = "Rejected"
		self.assertRaises(frappe.ValidationError, doc.save, ignore_permissions=True)

	def test_approved_record_immutable_for_non_system_manager(self):
		doc = self.make_attribution_case_doc().insert(ignore_permissions=True)
		doc.approval_state = "Submitted for Approval"
		doc.save(ignore_permissions=True)

		frappe.set_user(self.sponsor_user)
		doc.approval_state = "Approved"
		doc.save(ignore_permissions=True)

		frappe.set_user(self.owner_user)
		doc.reload()
		doc.attribution_summary = "Unauthorized mutation"
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

		doc = self.make_attribution_case_doc().insert(ignore_permissions=True)
		frappe.set_user(self.owner_user)
		transitioned = workflow_module.apply_workflow(doc, "Submit")
		self.assertEqual(transitioned.approval_state, "Submitted for Approval")

	def test_illegal_direct_transition_draft_to_approved_is_blocked(self):
		doc = self.make_attribution_case_doc().insert(ignore_permissions=True)
		frappe.set_user(self.sponsor_user)
		doc.approval_state = "Approved"
		self.assertRaises(frappe.ValidationError, doc.save, ignore_permissions=True)

	def test_insert_with_draft_succeeds(self):
		doc = self.make_attribution_case_doc()
		doc.approval_state = "Draft"
		inserted = doc.insert(ignore_permissions=True)
		self.assertEqual(inserted.approval_state, "Draft")

	def test_insert_with_submitted_fails(self):
		doc = self.make_attribution_case_doc()
		doc.approval_state = "Submitted for Approval"
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_owner_can_create_without_permission_bypass(self):
		frappe.set_user(self.owner_user)
		doc = self.make_attribution_case_doc().insert()
		self.assertEqual(doc.doctype, "Attribution Case")

	def test_sponsor_cannot_create_without_permission_bypass(self):
		frappe.set_user(self.sponsor_user)
		doc = self.make_attribution_case_doc()
		self.assertRaises(frappe.PermissionError, doc.insert)

	def test_operations_manager_cannot_write_without_permission_bypass(self):
		frappe.set_user("Administrator")
		doc = self.make_attribution_case_doc().insert()
		frappe.set_user(self.operations_user)
		doc.reload()
		doc.attribution_summary = "Ops manager edit attempt"
		self.assertRaises(frappe.PermissionError, doc.save)

	def test_register_report_exists_with_expected_access_roles(self):
		report = frappe.get_doc("Report", "Attribution Case Register")
		self.assertEqual(report.report_type, "Report Builder")
		self.assertEqual(report.ref_doctype, "Attribution Case")
		roles = {row.role for row in report.roles}
		self.assertTrue(
			{
				"System Manager",
				"EIP Workflow Owner",
				"EIP Executive Sponsor",
				"EIP Operations Manager",
			}.issubset(roles)
		)

	def test_empty_approval_state_is_normalized_to_draft(self):
		doc_save = self.make_attribution_case_doc().insert(ignore_permissions=True)
		doc_save.reload()
		doc_save.approval_state = ""
		doc_save.save()
		doc_save.reload()
		self.assertEqual(doc_save.approval_state, "Draft")

		doc_save_ignore = self.make_attribution_case_doc().insert(ignore_permissions=True)
		doc_save_ignore.reload()
		doc_save_ignore.approval_state = ""
		doc_save_ignore.save(ignore_permissions=True)
		doc_save_ignore.reload()
		self.assertEqual(doc_save_ignore.approval_state, "Draft")

		doc_insert = self.make_attribution_case_doc()
		doc_insert.approval_state = ""
		doc_insert.insert(ignore_permissions=True)
		doc_insert.reload()
		self.assertEqual(doc_insert.approval_state, "Draft")
