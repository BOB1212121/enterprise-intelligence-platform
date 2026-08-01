from unittest.mock import patch

import frappe
from frappe.desk.query_report import run as run_query_report
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, random_string, today

from enterprise_intelligence_platform.feature2_follow_through_orchestration import (
	Feature2FollowThroughItem,
	evaluate_feature2_prioritization,
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


class TestFeature2FollowThroughOrchestration(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		setup_s1_f1()
		setup_s1_f2()
		setup_s1_f3()
		setup_s2_f2()
		cls.ensure_feature2_report_configuration()

		cls.owner_user = cls.make_user_with_role("eip_feature2_owner@example.com", "EIP Workflow Owner")
		cls.sponsor_user = cls.make_user_with_role(
			"eip_feature2_sponsor@example.com", "EIP Executive Sponsor"
		)
		cls.operations_user = cls.make_user_with_role(
			"eip_feature2_operations@example.com", "EIP Operations Manager"
		)
		cls.system_manager_user = cls.make_user_with_role(
			"eip_feature2_system@example.com", "System Manager"
		)
		cls.unprivileged_user = cls.make_base_user("eip_feature2_unprivileged@example.com")

	@classmethod
	def ensure_feature2_report_configuration(cls):
		report_name = "Feature 2 Follow-Through Prioritization Review"
		if not frappe.db.exists("Report", report_name):
			report_doc = frappe.get_doc(
				{
					"doctype": "Report",
					"name": report_name,
					"report_name": report_name,
					"ref_doctype": "Decision Record",
					"report_type": "Script Report",
					"is_standard": "Yes",
					"module": "Enterprise Intelligence Platform",
				}
			)
			report_doc.db_insert(ignore_if_duplicate=True)
		else:
			frappe.db.set_value("Report", report_name, "ref_doctype", "Decision Record", update_modified=False)
			frappe.db.set_value("Report", report_name, "report_type", "Script Report", update_modified=False)
			frappe.db.set_value("Report", report_name, "is_standard", "Yes", update_modified=False)
			frappe.db.set_value(
				"Report", report_name, "module", "Enterprise Intelligence Platform", update_modified=False
			)

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
				"workflow_name": f"Feature 2 Charter {random_string(8)}",
				"business_objective": "Follow-through orchestration readiness.",
				"in_scope_definition": "Feature 2 identification and prioritization scope.",
				"accountable_owner": self.owner_user,
				"executive_sponsor": self.sponsor_user,
				"operating_cadence": "Weekly",
				"baseline_start_date": "2026-07-01",
				"baseline_end_date": "2026-08-31",
				"baseline_kpis": [
					{"kpi_code": "DRR", "baseline_value": 25, "data_source": "Baseline"},
					{"kpi_code": "DCT", "baseline_value": 14, "data_source": "Baseline"},
					{"kpi_code": "AER", "baseline_value": 80, "data_source": "Baseline"},
					{"kpi_code": "OCR", "baseline_value": 90, "data_source": "Baseline"},
					{"kpi_code": "RER", "baseline_value": 22, "data_source": "Baseline"},
				],
			}
		)

	def make_decision_doc(self, charter_name, *, approved=False):
		doc = frappe.get_doc(
			{
				"doctype": "Decision Record",
				"decision_title": f"Feature 2 Decision {random_string(8)}",
				"lighthouse_workflow_charter": charter_name,
				"accountable_owner": self.owner_user,
				"executive_sponsor": self.sponsor_user,
				"decision_type": "Operational",
				"decision_criticality": "High",
				"proposal_date": add_days(today(), -5),
				"target_decision_date": add_days(today(), 3),
				"business_decision_summary": "Feature 2 decision context.",
				"tradeoff_summary": "Tradeoff context.",
				"assumptions": [
					{
						"assumption_text": "Signals remain available.",
						"confidence_score": 0.8,
						"falsifiability_note": "Invalidate if data feed fails.",
					}
				],
			}
		).insert(ignore_permissions=True)

		if approved:
			doc.reload()
			doc.approval_state = "Submitted for Approval"
			doc.save(ignore_permissions=True)
			frappe.set_user(self.sponsor_user)
			doc.reload()
			doc.approval_state = "Approved"
			doc = doc.save(ignore_permissions=True)
			frappe.set_user("Administrator")

		return doc

	def make_dependency_doc(
		self,
		decision_name,
		*,
		criticality="Critical",
		status="Open",
		exception_required=1,
		target_resolution_offset_days=2,
	):
		return frappe.get_doc(
			{
				"doctype": "Dependency Exception Record",
				"dependency_title": f"Feature 2 Dependency {random_string(8)}",
				"decision_record": decision_name,
				"lighthouse_workflow_charter": frappe.get_doc("Decision Record", decision_name).lighthouse_workflow_charter,
				"accountable_owner": self.owner_user,
				"executive_sponsor": self.sponsor_user,
				"dependency_type": "System",
				"dependency_criticality": criticality,
				"declaration_date": add_days(today(), -2),
				"target_resolution_date": add_days(today(), target_resolution_offset_days),
				"dependency_status": status,
				"resolution_note": "Resolved" if status == "Resolved" else "",
				"dependency_description": "Feature 2 dependency signal.",
				"impact_summary": "Impacts prioritization.",
				"mitigation_plan": "Mitigation plan.",
				"exception_required": exception_required,
				"exception_owner": self.owner_user,
				"exception_reason": "Governed exception",
				"exception_expiry_date": add_days(today(), 20),
				"remediation_intent": "Resolve soon.",
			}
		).insert(ignore_permissions=True)

	def make_attribution_case_doc(self, decision_name, *, confidence_score=0.5, approved=False):
		dependency = self.make_dependency_doc(decision_name)
		doc = frappe.get_doc(
			{
				"doctype": "Attribution Case",
				"attribution_title": f"Feature 2 Attribution {random_string(8)}",
				"decision_record": decision_name,
				"lighthouse_workflow_charter": frappe.get_doc("Decision Record", decision_name).lighthouse_workflow_charter,
				"accountable_owner": self.owner_user,
				"executive_sponsor": self.sponsor_user,
				"observation_start_date": add_days(today(), -7),
				"observation_end_date": add_days(today(), -1),
				"attribution_summary": "Attribution signal summary.",
				"confounder_summary": "Confounder summary.",
				"confidence_score": confidence_score,
				"confidence_rationale": "Confidence rationale.",
				"attribution_chain_steps": [
					{
						"sequence_no": 1,
						"step_summary": "Chain step.",
						"dependency_exception_record": dependency.name,
					}
				],
				"attribution_evidence": [
					{
						"evidence_type": "Metric",
						"supports_claim": 1,
						"evidence_reference": "Reference",
						"evidence_date": add_days(today(), -1),
					}
				],
			}
		).insert(ignore_permissions=True)

		if approved:
			doc.reload()
			doc.approval_state = "Submitted for Approval"
			doc.save(ignore_permissions=True)
			frappe.set_user(self.sponsor_user)
			doc.reload()
			doc.approval_state = "Approved"
			doc = doc.save(ignore_permissions=True)
			frappe.set_user("Administrator")

		return doc

	def seed_follow_through_dataset(self):
		charter = self.make_charter_doc().insert(ignore_permissions=True)
		decision = self.make_decision_doc(charter.name, approved=False)

		unresolved_dependency = self.make_dependency_doc(
			decision.name,
			criticality="Critical",
			status="Open",
			exception_required=1,
			target_resolution_offset_days=1,
		)
		resolved_dependency = self.make_dependency_doc(
			decision.name,
			criticality="Medium",
			status="Resolved",
			exception_required=0,
			target_resolution_offset_days=10,
		)
		low_confidence_attr = self.make_attribution_case_doc(decision.name, confidence_score=0.4, approved=True)
		high_confidence_attr = self.make_attribution_case_doc(decision.name, confidence_score=0.9, approved=True)

		return {
			"charter": charter,
			"decision": decision,
			"unresolved_dependency": unresolved_dependency,
			"resolved_dependency": resolved_dependency,
			"low_confidence_attr": low_confidence_attr,
			"high_confidence_attr": high_confidence_attr,
		}

	def test_identification_and_prioritization_helper(self):
		seed = self.seed_follow_through_dataset()
		items = evaluate_feature2_prioritization(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE2_POLICY_V1",
		)
		self.assertTrue(items)
		types = {item.item_type for item in items}
		self.assertIn("Dependency Risk", types)
		self.assertIn("Decision Approval Readiness", types)
		self.assertIn("Attribution Confidence", types)
		self.assertTrue(all(item.source_link_integrity_confirmed == 1 for item in items))
		self.assertTrue(all(item.read_only_confirmed == 1 for item in items))

	def test_actor_trace_audit_evidence_is_recorded(self):
		seed = self.seed_follow_through_dataset()
		with patch("enterprise_intelligence_platform.feature2_follow_through_orchestration.frappe.logger") as logger_mock:
			evaluate_feature2_prioritization(
				lighthouse_workflow_charter=seed["charter"].name,
				review_window_start=add_days(today(), -30),
				review_window_end=add_days(today(), 30),
				policy_version="FEATURE2_POLICY_V1",
			)
			self.assertTrue(logger_mock.called)
			self.assertTrue(logger_mock.return_value.info.called)
			payload = logger_mock.return_value.info.call_args[0][0]
			self.assertEqual(payload["event"], "feature2_prioritization_review_executed")
			self.assertEqual(payload["source_charter"], seed["charter"].name)
			self.assertEqual(payload["governance_review_context"]["policy_version"], "FEATURE2_POLICY_V1")
			self.assertIn("actor", payload)
			self.assertIn("executed_at", payload)
			self.assertIn("requested_review_window", payload)

	def test_deterministic_ordering(self):
		seed = self.seed_follow_through_dataset()
		first = evaluate_feature2_prioritization(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE2_POLICY_V1",
		)
		second = evaluate_feature2_prioritization(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE2_POLICY_V1",
		)
		self.assertEqual([item.as_dict() for item in first], [item.as_dict() for item in second])

	def test_review_window_validation(self):
		seed = self.seed_follow_through_dataset()
		self.assertRaises(
			frappe.ValidationError,
			evaluate_feature2_prioritization,
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), 1),
			review_window_end=add_days(today(), -1),
			policy_version="FEATURE2_POLICY_V1",
		)

	def test_fr005_blocks_when_unresolved_baseline_change_trigger_exists(self):
		seed = self.seed_follow_through_dataset()
		with patch(
			"enterprise_intelligence_platform.feature2_follow_through_orchestration._detect_runtime_contract_mutation_risk",
			return_value=True,
		):
			self.assertRaises(
				frappe.ValidationError,
				evaluate_feature2_prioritization,
				lighthouse_workflow_charter=seed["charter"].name,
				review_window_start=add_days(today(), -30),
				review_window_end=add_days(today(), 30),
				policy_version="FEATURE2_POLICY_V1",
			)

	def test_fr008_detects_duplicate_source_of_truth_persistence_risk(self):
		seed = self.seed_follow_through_dataset()
		with patch(
			"enterprise_intelligence_platform.feature2_follow_through_orchestration._detect_duplicate_source_of_truth_persistence_risk",
			return_value=True,
		), patch(
			"enterprise_intelligence_platform.feature2_follow_through_orchestration._detect_ownership_mapping_mutation_risk",
			return_value=False,
		), patch(
			"enterprise_intelligence_platform.feature2_follow_through_orchestration._detect_runtime_contract_mutation_risk",
			return_value=False,
		):
			self.assertRaises(
				frappe.ValidationError,
				evaluate_feature2_prioritization,
				lighthouse_workflow_charter=seed["charter"].name,
				review_window_start=add_days(today(), -30),
				review_window_end=add_days(today(), 30),
				policy_version="FEATURE2_POLICY_V1",
			)

	def test_fr008_detects_ownership_mapping_mutation_risk(self):
		seed = self.seed_follow_through_dataset()
		report_name = "Feature 2 Follow-Through Prioritization Review"
		frappe.get_doc(
			{
				"doctype": "Has Role",
				"parent": report_name,
				"parenttype": "Report",
				"parentfield": "roles",
				"role": "Guest",
			}
		).insert(ignore_permissions=True)
		self.assertRaises(
			frappe.ValidationError,
			evaluate_feature2_prioritization,
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE2_POLICY_V1",
		)
		self.ensure_feature2_report_configuration()

	def test_orv_eps_non_duplication_failure_is_deterministic(self):
		seed = self.seed_follow_through_dataset()

		def invalid_items(*, decision, window_start, window_end, policy_version, parameters):
			return [
				Feature2FollowThroughItem(
					lighthouse_workflow_charter=decision.get("lighthouse_workflow_charter"),
					decision_record=decision.get("name"),
					review_window_start=window_start.isoformat(),
					review_window_end=window_end.isoformat(),
					policy_version=policy_version,
					item_type="Decision Approval Readiness",
					item_title="Boundary violation",
					source_doctype="Operational Review View",
					source_name="ORV-TEST",
					source_owner=decision.get("accountable_owner"),
					executive_sponsor=decision.get("executive_sponsor"),
					priority_score=100.0,
					priority_band="Critical",
					urgency_bucket="Overdue",
					source_link_integrity_confirmed=1,
					read_only_confirmed=1,
					non_duplication_boundary_confirmed=0,
					ranking_rationale="Injected violation",
					perf_max_ranking_execution_duration="PERF_MAX_RANKING_EXECUTION_DURATION",
					perf_min_items_per_review_window="PERF_MIN_ITEMS_PER_REVIEW_WINDOW",
					perf_ordering_stability_tolerance="PERF_ORDERING_STABILITY_TOLERANCE",
					perf_supported_ranking_dataset_profile="PERF_SUPPORTED_RANKING_DATASET_PROFILE",
					perf_degradation_policy_on_capacity_exceeded="PERF_DEGRADATION_POLICY_ON_CAPACITY_EXCEEDED",
					perf_supported_review_window_definition="PERF_SUPPORTED_REVIEW_WINDOW_DEFINITION",
				)
			]

		with patch(
			"enterprise_intelligence_platform.feature2_follow_through_orchestration._build_decision_items",
			side_effect=invalid_items,
		):
			self.assertRaises(
				frappe.ValidationError,
				evaluate_feature2_prioritization,
				lighthouse_workflow_charter=seed["charter"].name,
				review_window_start=add_days(today(), -30),
				review_window_end=add_days(today(), 30),
				policy_version="FEATURE2_POLICY_V1",
			)

	def test_data_retrieval_does_not_use_permission_bypass_for_record_reads(self):
		seed = self.seed_follow_through_dataset()
		original_get_all = frappe.get_all

		def guarded_get_all(doctype, *args, **kwargs):
			if doctype in {"Decision Record", "Dependency Exception Record", "Attribution Case"}:
				raise AssertionError(f"Permission-bypass path used for {doctype}")
			return original_get_all(doctype, *args, **kwargs)

		with patch("enterprise_intelligence_platform.feature2_follow_through_orchestration.frappe.get_all", side_effect=guarded_get_all):
			items = evaluate_feature2_prioritization(
				lighthouse_workflow_charter=seed["charter"].name,
				review_window_start=add_days(today(), -30),
				review_window_end=add_days(today(), 30),
				policy_version="FEATURE2_POLICY_V1",
			)
			self.assertTrue(items)

	def test_empty_dataset_returns_empty_result(self):
		charter = self.make_charter_doc().insert(ignore_permissions=True)
		items = evaluate_feature2_prioritization(
			lighthouse_workflow_charter=charter.name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE2_POLICY_V1",
		)
		self.assertEqual(items, tuple())

	def test_boundary_value_prioritization_buckets(self):
		charter = self.make_charter_doc().insert(ignore_permissions=True)
		decision = self.make_decision_doc(charter.name, approved=False)

		frappe.db.set_value("Decision Record", decision.name, "target_decision_date", add_days(today(), 7))
		items = evaluate_feature2_prioritization(
			lighthouse_workflow_charter=charter.name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE2_POLICY_V1",
		)
		decision_item = next(item for item in items if item.source_doctype == "Decision Record")
		self.assertEqual(decision_item.urgency_bucket, "Due within 7 days")

		frappe.db.set_value("Decision Record", decision.name, "target_decision_date", add_days(today(), 30))
		items = evaluate_feature2_prioritization(
			lighthouse_workflow_charter=charter.name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 31),
			policy_version="FEATURE2_POLICY_V1",
		)
		decision_item = next(item for item in items if item.source_doctype == "Decision Record")
		self.assertEqual(decision_item.urgency_bucket, "Due within 30 days")

		frappe.db.set_value("Decision Record", decision.name, "target_decision_date", add_days(today(), 31))
		items = evaluate_feature2_prioritization(
			lighthouse_workflow_charter=charter.name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 40),
			policy_version="FEATURE2_POLICY_V1",
		)
		decision_item = next(item for item in items if item.source_doctype == "Decision Record")
		self.assertEqual(decision_item.urgency_bucket, "Beyond 30 days")

	def test_invalid_acceptance_parameters_json_fails(self):
		seed = self.seed_follow_through_dataset()
		self.assertRaises(
			frappe.ValidationError,
			run_query_report,
			report_name="Feature 2 Follow-Through Prioritization Review",
			user=self.owner_user,
			filters={
				"lighthouse_workflow_charter": seed["charter"].name,
				"decision_record": seed["decision"].name,
				"review_window_start": add_days(today(), -30),
				"review_window_end": add_days(today(), 30),
				"policy_version": "FEATURE2_POLICY_V1",
				"acceptance_parameters_json": "{not-valid-json}",
			},
		)

	def test_ac008_custom_acceptance_parameters_require_approval_metadata(self):
		seed = self.seed_follow_through_dataset()
		self.assertRaises(
			frappe.ValidationError,
			evaluate_feature2_prioritization,
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE2_POLICY_V1",
			acceptance_parameters={"perf_max_ranking_execution_duration": "<=5s"},
		)

	def test_ac008_custom_acceptance_parameters_with_approved_metadata_pass(self):
		seed = self.seed_follow_through_dataset()
		items = evaluate_feature2_prioritization(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE2_POLICY_V1",
			acceptance_parameters={
				"perf_max_ranking_execution_duration": "<=5s",
				"approval_metadata": {
					"approval_status": "Approved",
					"approval_reference": "F2-AC008-APPROVAL-001",
					"approved_by_role": "EIP Executive Sponsor",
				},
			},
		)
		self.assertTrue(items)
		self.assertTrue(all(item.perf_max_ranking_execution_duration == "<=5s" for item in items))

	def test_strengthened_integrity_validation_fails_on_inconsistent_source_metadata(self):
		seed = self.seed_follow_through_dataset()
		frappe.db.set_value(
			"Dependency Exception Record",
			seed["unresolved_dependency"].name,
			"lighthouse_workflow_charter",
			"INVALID-CHARTER",
			update_modified=False,
		)
		self.assertRaises(
			frappe.ValidationError,
			evaluate_feature2_prioritization,
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE2_POLICY_V1",
		)

	def test_report_executes_via_desk_for_governance_roles(self):
		seed = self.seed_follow_through_dataset()
		for user in (self.owner_user, self.sponsor_user, self.operations_user, self.system_manager_user):
			payload = run_query_report(
				report_name="Feature 2 Follow-Through Prioritization Review",
				user=user,
				filters={
					"lighthouse_workflow_charter": seed["charter"].name,
					"decision_record": seed["decision"].name,
					"review_window_start": add_days(today(), -30),
					"review_window_end": add_days(today(), 30),
					"policy_version": "FEATURE2_POLICY_V1",
				},
			)
			self.assertIn("result", payload)
			self.assertTrue(payload["result"])
			self.assertTrue(all(row["non_duplication_boundary_confirmed"] == 1 for row in payload["result"]))

	def test_permission_enforcement_for_unprivileged_user(self):
		seed = self.seed_follow_through_dataset()
		frappe.set_user(self.unprivileged_user)
		self.assertRaises(
			frappe.PermissionError,
			run_query_report,
			report_name="Feature 2 Follow-Through Prioritization Review",
			filters={
				"lighthouse_workflow_charter": seed["charter"].name,
				"decision_record": seed["decision"].name,
				"review_window_start": add_days(today(), -30),
				"review_window_end": add_days(today(), 30),
				"policy_version": "FEATURE2_POLICY_V1",
			},
		)

	def test_baseline_records_are_not_mutated(self):
		seed = self.seed_follow_through_dataset()
		decision_before = frappe.get_value(
			"Decision Record",
			seed["decision"].name,
			["approval_state", "modified"],
			as_dict=True,
		)
		dependency_before = frappe.get_value(
			"Dependency Exception Record",
			seed["unresolved_dependency"].name,
			["dependency_status", "modified"],
			as_dict=True,
		)
		attribution_before = frappe.get_value(
			"Attribution Case",
			seed["low_confidence_attr"].name,
			["approval_state", "modified"],
			as_dict=True,
		)
		evaluate_feature2_prioritization(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE2_POLICY_V1",
		)
		decision_after = frappe.get_value(
			"Decision Record",
			seed["decision"].name,
			["approval_state", "modified"],
			as_dict=True,
		)
		dependency_after = frappe.get_value(
			"Dependency Exception Record",
			seed["unresolved_dependency"].name,
			["dependency_status", "modified"],
			as_dict=True,
		)
		attribution_after = frappe.get_value(
			"Attribution Case",
			seed["low_confidence_attr"].name,
			["approval_state", "modified"],
			as_dict=True,
		)
		self.assertEqual(decision_before.approval_state, decision_after.approval_state)
		self.assertEqual(dependency_before.dependency_status, dependency_after.dependency_status)
		self.assertEqual(attribution_before.approval_state, attribution_after.approval_state)
