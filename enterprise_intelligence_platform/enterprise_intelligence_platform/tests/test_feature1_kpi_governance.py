import json
from copy import deepcopy

import frappe
from frappe.desk.query_report import run as run_query_report
from frappe.tests.utils import FrappeTestCase
from frappe.utils import random_string

from enterprise_intelligence_platform.feature1_kpi_governance import (
	MANDATORY_EVIDENCE_ITEMS,
	REQUIRED_KPI_CODES,
	calculate_evidence_result,
	calculate_comparative_result,
	calculate_kpi_result,
	evaluate_feature1_review,
)
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


class TestFeature1KpiGovernance(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		setup_s1_f1()
		setup_s1_f2()
		setup_s1_f3()
		setup_s2_f2()
		cls.ensure_feature1_report_configuration()

		cls.owner_user = cls.make_user_with_role("eip_feature1_owner@example.com", "EIP Workflow Owner")
		cls.sponsor_user = cls.make_user_with_role(
			"eip_feature1_sponsor@example.com", "EIP Executive Sponsor"
		)
		cls.operations_user = cls.make_user_with_role(
			"eip_feature1_operations@example.com", "EIP Operations Manager"
		)
		cls.make_user_with_role(cls.owner_user, "System Manager")
		cls.make_user_with_role(cls.sponsor_user, "System Manager")
		cls.make_user_with_role(cls.operations_user, "System Manager")
		cls.system_manager_user = cls.make_user_with_role(
			"eip_feature1_system@example.com", "System Manager"
		)
		cls.unprivileged_user = cls.make_base_user("eip_feature1_unprivileged@example.com")

	@classmethod
	def ensure_feature1_report_configuration(cls):
		report_name = "Feature 1 KPI Governance Review"
		frappe.db.set_value("Report", report_name, "ref_doctype", "Decision Record", update_modified=False)
		frappe.db.delete(
			"Has Role",
			{"parent": report_name, "parenttype": "Report", "parentfield": "roles"},
		)
		for idx, role in enumerate(
			("System Manager", "EIP Workflow Owner", "EIP Executive Sponsor", "EIP Operations Manager"),
			start=1,
		):
			frappe.get_doc(
				{
					"doctype": "Has Role",
					"parent": report_name,
					"parenttype": "Report",
					"parentfield": "roles",
					"idx": idx,
					"role": role,
				}
			).insert(ignore_permissions=True)
		frappe.clear_cache()

	def tearDown(self):
		frappe.set_user("Administrator")

	@staticmethod
	def make_base_user(email: str) -> str:
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
		return email

	@classmethod
	def make_user_with_role(cls, email: str, role: str) -> str:
		cls.make_base_user(email)
		exists = frappe.db.exists(
			"Has Role",
			{
				"parent": email,
				"parenttype": "User",
				"parentfield": "roles",
				"role": role,
			},
		)
		if not exists:
			frappe.get_doc(
				{
					"doctype": "Has Role",
					"parent": email,
					"parenttype": "User",
					"parentfield": "roles",
					"role": role,
				}
			).insert(ignore_permissions=True)
		frappe.clear_cache(user=email)
		return email

	def make_charter_doc(self):
		return frappe.get_doc(
			{
				"doctype": "Lighthouse Workflow Charter",
				"workflow_name": f"Feature 1 Charter {random_string(8)}",
				"business_objective": "Govern KPI readiness for Feature 1.",
				"in_scope_definition": "Feature 1 governance review scope.",
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
		)

	def make_decision_doc(self, charter_name):
		return frappe.get_doc(
			{
				"doctype": "Decision Record",
				"decision_title": f"Feature 1 Decision {random_string(8)}",
				"lighthouse_workflow_charter": charter_name,
				"accountable_owner": self.owner_user,
				"executive_sponsor": self.sponsor_user,
				"decision_type": "Operational",
				"decision_criticality": "Medium",
				"proposal_date": "2026-07-15",
				"target_decision_date": "2026-07-20",
				"business_decision_summary": "Confirm governance thresholds.",
				"tradeoff_summary": "Balance certainty and review effort.",
				"assumptions": [
					{
						"assumption_text": "Approved planning weights remain stable.",
						"confidence_score": 0.8,
						"falsifiability_note": "Invalidate if weight model changes.",
					}
				],
			}
		)

	def make_dependency_doc(self, decision_name):
		return frappe.get_doc(
			{
				"doctype": "Dependency Exception Record",
				"dependency_title": f"Feature 1 Dependency {random_string(8)}",
				"decision_record": decision_name,
				"lighthouse_workflow_charter": frappe.get_doc("Decision Record", decision_name).lighthouse_workflow_charter,
				"accountable_owner": self.owner_user,
				"executive_sponsor": self.sponsor_user,
				"dependency_type": "System",
				"dependency_criticality": "Medium",
				"declaration_date": "2026-07-18",
				"target_resolution_date": "2026-07-25",
				"dependency_status": "Resolved",
				"resolution_note": "Resolved for Feature 1 governance review.",
				"dependency_description": "Feature 1 evidence dependency.",
				"impact_summary": "Supports evidence review.",
				"mitigation_plan": "Standard governance review.",
				"exception_required": 1,
				"exception_owner": self.owner_user,
				"exception_reason": "Controlled evidence review.",
				"exception_expiry_date": "2026-07-30",
				"remediation_intent": "Remove after review.",
			}
		)

	def make_attribution_case_doc(self, decision_name):
		dependency = self.make_dependency_doc(decision_name).insert(ignore_permissions=True)
		return frappe.get_doc(
			{
				"doctype": "Attribution Case",
				"attribution_title": f"Feature 1 Attribution {random_string(8)}",
				"decision_record": decision_name,
				"lighthouse_workflow_charter": frappe.get_doc("Decision Record", decision_name).lighthouse_workflow_charter,
				"accountable_owner": self.owner_user,
				"executive_sponsor": self.sponsor_user,
				"observation_start_date": "2026-07-20",
				"observation_end_date": "2026-07-25",
				"attribution_summary": "Governance evidence supports the review.",
				"confounder_summary": "No major confounders.",
				"confidence_score": 0.7,
				"confidence_rationale": "Evidence and governance signals align.",
				"attribution_chain_steps": [
					{
						"sequence_no": 1,
						"step_summary": "Decision executed and reviewed.",
						"dependency_exception_record": dependency.name,
					}
				],
				"attribution_evidence": [
					{
						"evidence_type": "Metric",
						"supports_claim": 1,
						"evidence_reference": "Feature 1 KPI evidence",
						"evidence_date": "2026-07-25",
						"evidence_note": "Supports the review package.",
					}
				],
			}
		)

	def make_approved_package(self):
		charter = self.make_charter_doc().insert(ignore_permissions=True)
		charter.reload()
		charter.approval_state = "Submitted for Sponsor Approval"
		charter.save(ignore_permissions=True)
		frappe.set_user(self.sponsor_user)
		charter.reload()
		charter.approval_state = "Baseline Accepted"
		charter = charter.save(ignore_permissions=True)

		frappe.set_user("Administrator")
		decision = self.make_decision_doc(charter.name).insert(ignore_permissions=True)
		decision.reload()
		decision.approval_state = "Submitted for Approval"
		decision.save(ignore_permissions=True)
		frappe.set_user(self.sponsor_user)
		decision.reload()
		decision.approval_state = "Approved"
		decision = decision.save(ignore_permissions=True)

		frappe.set_user("Administrator")
		dependency = self.make_dependency_doc(decision.name).insert(ignore_permissions=True)
		dependency.reload()
		dependency.approval_state = "Submitted for Approval"
		dependency.save(ignore_permissions=True)
		frappe.set_user(self.sponsor_user)
		dependency.reload()
		dependency.approval_state = "Approved"
		dependency = dependency.save(ignore_permissions=True)

		frappe.set_user("Administrator")
		attribution = self.make_attribution_case_doc(decision.name).insert(ignore_permissions=True)
		attribution.reload()
		attribution.approval_state = "Submitted for Approval"
		attribution.save(ignore_permissions=True)
		frappe.set_user(self.sponsor_user)
		attribution.reload()
		attribution.approval_state = "Approved"
		attribution = attribution.save(ignore_permissions=True)

		return {
			"charter": charter,
			"decision": decision,
			"dependency": dependency,
			"attribution": attribution,
		}

	def make_review_package(self, seed, candidate_a_score=95, candidate_b_score=80, weighting_model="Approved planning weights"):
		return {
			"kpi_matrix": [
				{
					"kpi_code": "DRR",
					"formula": "Resolved dependency count / total dependency count",
					"source_owner": self.owner_user,
					"measurement_window": {"start": "2026-07-01", "end": "2026-07-20"},
					"threshold": 95.0,
					"pass_fail_rule": "Pass when resolution ratio meets threshold.",
					"baseline_value": 25,
				},
				{
					"kpi_code": "DCT",
					"formula": "Median days to closure within baseline window",
					"source_owner": self.owner_user,
					"measurement_window": {"start": "2026-07-01", "end": "2026-07-20"},
					"threshold": 14.0,
					"pass_fail_rule": "Pass when median closure time is at or below threshold.",
					"baseline_value": 14,
				},
				{
					"kpi_code": "AER",
					"formula": "Approved attribution count / total attribution count",
					"source_owner": self.sponsor_user,
					"measurement_window": {"start": "2026-07-01", "end": "2026-07-20"},
					"threshold": 80.0,
					"pass_fail_rule": "Pass when attribution approval ratio meets threshold.",
					"baseline_value": 80,
				},
				{
					"kpi_code": "OCR",
					"formula": "On-time closure count / total closure count",
					"source_owner": self.operations_user,
					"measurement_window": {"start": "2026-07-01", "end": "2026-07-20"},
					"threshold": 90.0,
					"pass_fail_rule": "Pass when on-time closure ratio meets threshold.",
					"baseline_value": 90,
				},
				{
					"kpi_code": "RER",
					"formula": "Resolved exception count / total exception count",
					"source_owner": self.owner_user,
					"measurement_window": {"start": "2026-07-01", "end": "2026-07-20"},
					"threshold": 22.0,
					"pass_fail_rule": "Pass when resolved exception ratio meets threshold.",
					"baseline_value": 22,
				},
			],
			"comparative_assessment": {
				"weighting_model": weighting_model,
				"dimensions": [
					{
						"name": "Execution accountability",
						"weight": 40.0,
						"candidate_a_score": candidate_a_score,
						"candidate_b_score": candidate_b_score,
					},
					{
						"name": "Decision responsiveness",
						"weight": 35.0,
						"candidate_a_score": candidate_a_score,
						"candidate_b_score": candidate_b_score,
					},
					{
						"name": "Governance confidence",
						"weight": 25.0,
						"candidate_a_score": candidate_a_score,
						"candidate_b_score": candidate_b_score,
					},
				],
			},
			"evidence_package": [
				{"label": "KPI matrix", "reviewable": True, "source_reference": "Feature 1 KPI matrix"},
				{
					"label": "Comparative assessment matrix",
					"reviewable": True,
					"source_reference": "Feature 1 comparative assessment matrix",
				},
				{"label": "Risk assessment status", "reviewable": True, "source_reference": seed["dependency"].name},
				{
					"label": "Architecture impact review evidence",
					"reviewable": True,
					"source_reference": seed["decision"].name,
				},
				{
					"label": "Baseline compatibility review evidence",
					"reviewable": True,
					"source_reference": seed["charter"].name,
				},
				{
					"label": "Active gate evidence package",
					"reviewable": True,
					"source_reference": "Governance approver votes",
				},
			],
			"approver_votes": [
				{"role": "EIP Workflow Owner", "user": self.owner_user, "approved": True},
				{"role": "EIP Executive Sponsor", "user": self.sponsor_user, "approved": True},
				{"role": "EIP Operations Manager", "user": self.operations_user, "approved": True},
			],
		}

	def make_review_package_copy(self, seed, **overrides):
		package = deepcopy(self.make_review_package(seed, **{k: v for k, v in overrides.items() if k in {"candidate_a_score", "candidate_b_score", "weighting_model"}}))
		if "drop_kpi_formula" in overrides:
			package["kpi_matrix"][0].pop("formula", None)
		if "drop_approver_role" in overrides:
			role = overrides["drop_approver_role"]
			package["approver_votes"] = [vote for vote in package["approver_votes"] if vote["role"] != role]
		if "reviewable_labels" in overrides:
			reviewable_labels = set(overrides["reviewable_labels"])
			for item in package["evidence_package"]:
				item["reviewable"] = item["label"] in reviewable_labels
		return package

	def test_helper_go_path(self):
		seed = self.make_approved_package()
		result = evaluate_feature1_review(
			lighthouse_workflow_charter=seed["charter"].name,
			decision_record=seed["decision"].name,
			governance_package=self.make_review_package(seed),
		)
		self.assertEqual(result.review_outcome, "GO")
		self.assertEqual(result.baseline_change_trigger, 0)
		self.assertEqual(result.mandatory_evidence_present, len(MANDATORY_EVIDENCE_ITEMS))
		self.assertEqual(result.kpi_completeness_pct, 100.0)
		self.assertGreaterEqual(result.evidence_completeness_pct, 95.0)
		self.assertEqual(result.approver_unanimity_confirmed, 1)
		self.assertAlmostEqual(result.weighted_candidate_a_score, 95.0)
		self.assertAlmostEqual(result.weighted_candidate_b_score, 80.0)

	def test_kpi_matrix_enforcement_rejects_missing_formula(self):
		seed = self.make_approved_package()
		package = self.make_review_package_copy(seed, drop_kpi_formula=True)
		result = evaluate_feature1_review(
			lighthouse_workflow_charter=seed["charter"].name,
			decision_record=seed["decision"].name,
			governance_package=package,
		)
		self.assertLess(result.kpi_completeness_pct, 100.0)
		self.assertEqual(result.review_outcome, "NO-GO")

	def test_comparative_weighting_helper(self):
		seed = self.make_approved_package()
		package = self.make_review_package(seed, candidate_a_score=96, candidate_b_score=81)
		comparative = calculate_comparative_result(package["comparative_assessment"])
		self.assertEqual(comparative.completeness_pct, 100.0)
		self.assertGreater(comparative.weighted_candidate_a_score, comparative.weighted_candidate_b_score)
		self.assertAlmostEqual(comparative.comparative_delta, 15.0)

	def test_helper_no_go_when_evidence_is_missing(self):
		seed = self.make_approved_package()
		package = self.make_review_package(seed)
		package["evidence_package"] = [item for item in package["evidence_package"] if item["label"] != "Comparative assessment matrix"]
		result = evaluate_feature1_review(
			lighthouse_workflow_charter=seed["charter"].name,
			decision_record=seed["decision"].name,
			governance_package=package,
		)
		self.assertEqual(result.review_outcome, "NO-GO")
		self.assertLess(result.evidence_completeness_pct, 90.0)
		self.assertIn("Evidence completeness is below the mandatory review minimum", result.adjudication_reason)

	def test_helper_no_go_when_baseline_change_trigger_is_present(self):
		seed = self.make_approved_package()
		result = evaluate_feature1_review(
			lighthouse_workflow_charter=seed["charter"].name,
			decision_record=seed["decision"].name,
			governance_package=self.make_review_package(seed),
			baseline_change_trigger=True,
		)
		self.assertEqual(result.review_outcome, "NO-GO")
		self.assertEqual(result.baseline_change_trigger, 1)
		self.assertIn("ADR disposition", result.adjudication_reason)

	def test_kpi_completeness_helper(self):
		seed = self.make_approved_package()
		kpi_result = calculate_kpi_result(seed["charter"], self.make_review_package(seed)["kpi_matrix"])
		self.assertEqual(kpi_result.completeness_pct, 100.0)
		self.assertEqual(set(kpi_result.observed_codes), set(REQUIRED_KPI_CODES))

	def test_evidence_completeness_helper(self):
		seed = self.make_approved_package()
		package = self.make_review_package(seed)
		kpi_result = calculate_kpi_result(seed["charter"], package["kpi_matrix"])
		comparative = calculate_comparative_result(package["comparative_assessment"])
		related = evaluate_feature1_review(
			lighthouse_workflow_charter=seed["charter"].name,
			decision_record=seed["decision"].name,
			governance_package=package,
		)
		self.assertEqual(related.mandatory_evidence_total, len(MANDATORY_EVIDENCE_ITEMS))
		self.assertEqual(related.mandatory_evidence_present, len(MANDATORY_EVIDENCE_ITEMS))
		self.assertEqual(kpi_result.completeness_pct, 100.0)
		self.assertEqual(comparative.completeness_pct, 100.0)

	def test_mandatory_review_band_requires_unanimity(self):
		seed = self.make_approved_package()
		package = self.make_review_package(seed, candidate_a_score=85, candidate_b_score=80)
		result = evaluate_feature1_review(
			lighthouse_workflow_charter=seed["charter"].name,
			decision_record=seed["decision"].name,
			governance_package=package,
		)
		self.assertEqual(result.review_band_flag, 1)
		self.assertEqual(result.review_outcome, "GO")

	def test_approver_unanimity_required(self):
		seed = self.make_approved_package()
		package = self.make_review_package_copy(seed, candidate_a_score=85, candidate_b_score=80, drop_approver_role="EIP Operations Manager")
		result = evaluate_feature1_review(
			lighthouse_workflow_charter=seed["charter"].name,
			decision_record=seed["decision"].name,
			governance_package=package,
		)
		self.assertEqual(result.review_band_flag, 1)
		self.assertEqual(result.approver_unanimity_confirmed, 0)
		self.assertEqual(result.review_outcome, "NO-GO")

	def test_review_determinism(self):
		seed = self.make_approved_package()
		package = self.make_review_package(seed)
		first = evaluate_feature1_review(
			lighthouse_workflow_charter=seed["charter"].name,
			decision_record=seed["decision"].name,
			governance_package=package,
		)
		second = evaluate_feature1_review(
			lighthouse_workflow_charter=seed["charter"].name,
			decision_record=seed["decision"].name,
			governance_package=package,
		)
		self.assertEqual(first.as_dict(), second.as_dict())

	def test_report_executes_via_desk(self):
		seed = self.make_approved_package()
		governance_package_json = json.dumps(self.make_review_package(seed))
		frappe.set_user("Administrator")
		role_map = {
			self.owner_user: "EIP Workflow Owner",
			self.sponsor_user: "EIP Executive Sponsor",
			self.operations_user: "EIP Operations Manager",
		}
		for user, intended_role in role_map.items():
			self.assertIn(intended_role, frappe.get_roles(user))
			payload = run_query_report(
				report_name="Feature 1 KPI Governance Review",
				user=user,
				filters={
					"lighthouse_workflow_charter": seed["charter"].name,
					"decision_record": seed["decision"].name,
					"governance_package_json": governance_package_json,
				},
			)
			self.assertIn("result", payload)
			self.assertTrue(payload["result"])
			self.assertEqual(payload["result"][0]["review_outcome"], "GO")
			self.assertEqual(payload["result"][0]["approver_unanimity_confirmed"], 1)

	def test_permission_enforcement(self):
		seed = self.make_approved_package()
		frappe.set_user(self.unprivileged_user)
		self.assertRaises(
			frappe.PermissionError,
			run_query_report,
			report_name="Feature 1 KPI Governance Review",
			filters={
				"lighthouse_workflow_charter": seed["charter"].name,
				"decision_record": seed["decision"].name,
				"candidate_a_score": 95,
				"candidate_b_score": 80,
				"comparative_weighting_model": "Approved planning weights",
			},
		)
