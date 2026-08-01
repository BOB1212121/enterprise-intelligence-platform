from unittest.mock import patch

import frappe
from frappe.desk.query_report import run as run_query_report
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, random_string, today

from enterprise_intelligence_platform import feature3a_follow_through_lifecycle_orchestration as feature3a
from enterprise_intelligence_platform.feature3a_follow_through_lifecycle_orchestration import (
	evaluate_feature3a_lifecycle_governance,
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


class TestFeature3AFollowThroughLifecycleOrchestration(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		setup_s1_f1()
		setup_s1_f2()
		setup_s1_f3()
		setup_s2_f2()
		cls.ensure_feature3a_report_configuration()

		cls.owner_user = cls.make_user_with_role("eip_feature3a_owner@example.com", "EIP Workflow Owner")
		cls.sponsor_user = cls.make_user_with_role("eip_feature3a_sponsor@example.com", "EIP Executive Sponsor")
		cls.operations_user = cls.make_user_with_role(
			"eip_feature3a_operations@example.com", "EIP Operations Manager"
		)
		cls.system_manager_user = cls.make_user_with_role("eip_feature3a_system@example.com", "System Manager")
		cls.unprivileged_user = cls.make_base_user("eip_feature3a_unprivileged@example.com")

	@classmethod
	def ensure_feature3a_report_configuration(cls):
		report_name = "Feature 3A Follow-Through Lifecycle Governance Review"
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
				"workflow_name": f"Feature 3A Charter {random_string(8)}",
				"business_objective": "Follow-through lifecycle governance readiness.",
				"in_scope_definition": "Feature 3A lifecycle/escalation/closure governance.",
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

	def make_decision_doc(self, charter_name):
		return frappe.get_doc(
			{
				"doctype": "Decision Record",
				"decision_title": f"Feature 3A Decision {random_string(8)}",
				"lighthouse_workflow_charter": charter_name,
				"accountable_owner": self.owner_user,
				"executive_sponsor": self.sponsor_user,
				"decision_type": "Operational",
				"decision_criticality": "High",
				"proposal_date": add_days(today(), -5),
				"target_decision_date": add_days(today(), 3),
				"business_decision_summary": "Feature 3A decision context.",
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
				"dependency_title": f"Feature 3A Dependency {random_string(8)}",
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
				"dependency_description": "Feature 3A dependency signal.",
				"impact_summary": "Impacts lifecycle governance.",
				"mitigation_plan": "Mitigation plan.",
				"exception_required": exception_required,
				"exception_owner": self.owner_user,
				"exception_reason": "Governed exception",
				"exception_expiry_date": add_days(today(), 20),
				"remediation_intent": "Resolve soon.",
			}
		).insert(ignore_permissions=True)

	def make_attribution_case_doc(self, decision_name, *, confidence_score=0.5, dependency_name: str):
		return frappe.get_doc(
			{
				"doctype": "Attribution Case",
				"attribution_title": f"Feature 3A Attribution {random_string(8)}",
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
						"dependency_exception_record": dependency_name,
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

	def seed_dataset(self):
		charter = self.make_charter_doc().insert(ignore_permissions=True)
		decision = self.make_decision_doc(charter.name)
		dependency = self.make_dependency_doc(decision.name, criticality="Critical", status="Open", exception_required=1)
		attribution = self.make_attribution_case_doc(
			decision.name,
			confidence_score=0.5,
			dependency_name=dependency.name,
		)
		return {
			"charter": charter,
			"decision": decision,
			"dependency": dependency,
			"attribution": attribution,
		}

	def test_transition_identified_to_prioritized_is_allowed_for_owner(self):
		seed = self.seed_dataset()
		items = evaluate_feature3a_lifecycle_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE3A_POLICY_V1",
			decision_record=seed["decision"].name,
			lifecycle_context={
				"current_state": "Identified",
				"requested_action": "Prioritize",
				"governance_rationale": "Initial lifecycle progression.",
			},
		)
		self.assertEqual(len(items), 1)
		self.assertEqual(items[0].transition_allowed, 1)
		self.assertEqual(items[0].next_state, "Prioritized")

	def test_invalid_transition_is_blocked(self):
		seed = self.seed_dataset()
		items = evaluate_feature3a_lifecycle_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE3A_POLICY_V1",
			decision_record=seed["decision"].name,
			lifecycle_context={
				"current_state": "Identified",
				"requested_action": "Close",
			},
		)
		self.assertEqual(items[0].transition_allowed, 0)
		self.assertEqual(items[0].next_state, "Identified")

	def test_escalation_trigger_detected_from_open_critical_dependency(self):
		seed = self.seed_dataset()
		items = evaluate_feature3a_lifecycle_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE3A_POLICY_V1",
			decision_record=seed["decision"].name,
			lifecycle_context={
				"current_state": "In Progress",
				"requested_action": "Escalate",
				"manual_escalation_requested": 1,
			},
		)
		self.assertEqual(items[0].escalation_required, 1)

	def test_deescalation_requires_clear_request_and_no_active_escalation_risk(self):
		seed = self.seed_dataset()
		frappe.db.set_value("Dependency Exception Record", seed["dependency"].name, "dependency_status", "Resolved")
		frappe.db.set_value("Attribution Case", seed["attribution"].name, "confidence_score", 0.9)

		items = evaluate_feature3a_lifecycle_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE3A_POLICY_V1",
			decision_record=seed["decision"].name,
			lifecycle_context={
				"current_state": "Escalated",
				"requested_action": "Deescalate",
				"manual_escalation_clear_requested": 1,
				"completed_checkpoints": [
					"owner_resolution_note",
					"dependency_mitigation_evidence",
					"attribution_reconciliation_evidence",
				],
			},
		)
		self.assertEqual(items[0].escalation_required, 0)
		self.assertEqual(items[0].escalation_clear_allowed, 1)
		self.assertEqual(items[0].transition_allowed, 1)
		self.assertEqual(items[0].next_state, "In Progress")

	def test_deescalation_denied_when_checkpoints_incomplete(self):
		seed = self.seed_dataset()
		frappe.db.set_value("Dependency Exception Record", seed["dependency"].name, "dependency_status", "Resolved")
		frappe.db.set_value("Attribution Case", seed["attribution"].name, "confidence_score", 0.9)

		items = evaluate_feature3a_lifecycle_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE3A_POLICY_V1",
			decision_record=seed["decision"].name,
			lifecycle_context={
				"current_state": "Escalated",
				"requested_action": "Deescalate",
				"manual_escalation_clear_requested": 1,
				"completed_checkpoints": ["owner_resolution_note"],
			},
		)
		self.assertEqual(items[0].escalation_required, 0)
		self.assertEqual(items[0].resolution_checkpoints_complete, 0)
		self.assertEqual(items[0].escalation_clear_allowed, 0)
		self.assertEqual(items[0].transition_allowed, 0)
		self.assertEqual(items[0].next_state, "Escalated")

	def test_closure_requires_checkpoints_and_evidence(self):
		seed = self.seed_dataset()
		frappe.db.set_value("Dependency Exception Record", seed["dependency"].name, "dependency_status", "Resolved")
		frappe.db.set_value("Attribution Case", seed["attribution"].name, "confidence_score", 0.9)

		blocked = evaluate_feature3a_lifecycle_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE3A_POLICY_V1",
			decision_record=seed["decision"].name,
			lifecycle_context={
				"current_state": "Resolved",
				"requested_action": "Close",
				"completed_checkpoints": ["owner_resolution_note"],
				"closure_evidence_links": [["Decision Record", seed["decision"].name]],
			},
		)
		self.assertEqual(blocked[0].closure_allowed, 0)
		self.assertEqual(blocked[0].transition_allowed, 0)

		allowed = evaluate_feature3a_lifecycle_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE3A_POLICY_V1",
			decision_record=seed["decision"].name,
			lifecycle_context={
				"current_state": "Resolved",
				"requested_action": "Close",
				"completed_checkpoints": [
					"owner_resolution_note",
					"dependency_mitigation_evidence",
					"attribution_reconciliation_evidence",
				],
				"closure_evidence_links": [
					["Decision Record", seed["decision"].name],
					["Dependency Exception Record", seed["dependency"].name],
					["Attribution Case", seed["attribution"].name],
				],
			},
		)
		self.assertEqual(allowed[0].closure_evidence_complete, 1)
		self.assertEqual(allowed[0].closure_allowed, 1)
		self.assertEqual(allowed[0].next_state, "Closed")

	def test_invalid_lifecycle_context_json_fails(self):
		seed = self.seed_dataset()
		self.assertRaises(
			frappe.ValidationError,
			run_query_report,
			report_name="Feature 3A Follow-Through Lifecycle Governance Review",
			user=self.owner_user,
			filters={
				"lighthouse_workflow_charter": seed["charter"].name,
				"decision_record": seed["decision"].name,
				"review_window_start": add_days(today(), -30),
				"review_window_end": add_days(today(), 30),
				"policy_version": "FEATURE3A_POLICY_V1",
				"lifecycle_context_json": "{not-valid-json}",
			},
		)

	def test_unresolved_baseline_change_trigger_blocks_feature3a(self):
		seed = self.seed_dataset()
		with patch(
			"enterprise_intelligence_platform.feature3a_follow_through_lifecycle_orchestration._detect_runtime_contract_mutation_risk",
			return_value=True,
		):
			with self.assertRaises(frappe.ValidationError) as exc_info:
				evaluate_feature3a_lifecycle_governance(
					lighthouse_workflow_charter=seed["charter"].name,
					review_window_start=add_days(today(), -30),
					review_window_end=add_days(today(), 30),
					policy_version="FEATURE3A_POLICY_V1",
				)
			self.assertIn("adr_route_required=1", str(exc_info.exception))
			self.assertIn("baseline_change_trigger_blocked=1", str(exc_info.exception))

	def test_baseline_change_governance_signal_is_zero_when_no_trigger(self):
		with patch.object(feature3a, "_detect_duplicate_source_of_truth_persistence_risk", return_value=False), patch.object(
			feature3a, "_detect_ownership_mapping_mutation_risk", return_value=False
		), patch.object(feature3a, "_detect_runtime_contract_mutation_risk", return_value=False):
			blocked, adr_route_required, unresolved = feature3a._evaluate_baseline_change_governance_signal()
			self.assertEqual(blocked, 0)
			self.assertEqual(adr_route_required, 0)
			self.assertEqual(unresolved, tuple())

	def test_baseline_change_governance_signal_is_one_when_trigger_present(self):
		with patch.object(feature3a, "_detect_duplicate_source_of_truth_persistence_risk", return_value=True), patch.object(
			feature3a, "_detect_ownership_mapping_mutation_risk", return_value=False
		), patch.object(feature3a, "_detect_runtime_contract_mutation_risk", return_value=False):
			blocked, adr_route_required, unresolved = feature3a._evaluate_baseline_change_governance_signal()
			self.assertEqual(blocked, 1)
			self.assertEqual(adr_route_required, 1)
			self.assertTrue(unresolved)

	def test_baseline_change_governance_signal_is_deterministic(self):
		with patch.object(feature3a, "_detect_duplicate_source_of_truth_persistence_risk", return_value=False), patch.object(
			feature3a, "_detect_ownership_mapping_mutation_risk", return_value=False
		), patch.object(feature3a, "_detect_runtime_contract_mutation_risk", return_value=False):
			first = feature3a._evaluate_baseline_change_governance_signal()
			second = feature3a._evaluate_baseline_change_governance_signal()
			self.assertEqual(first, second)

	def test_runtime_output_signals_zero_when_no_trigger(self):
		seed = self.seed_dataset()
		items = evaluate_feature3a_lifecycle_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE3A_POLICY_V1",
			decision_record=seed["decision"].name,
			lifecycle_context={
				"current_state": "Identified",
				"requested_action": "Prioritize",
			},
		)
		self.assertEqual(items[0].adr_route_required, 0)
		self.assertEqual(items[0].baseline_change_trigger_blocked, 0)

	def test_deterministic_behavior(self):
		seed = self.seed_dataset()
		context = {
			"current_state": "In Progress",
			"requested_action": "Escalate",
			"manual_escalation_requested": 1,
			"completed_checkpoints": ["owner_resolution_note"],
			"governance_rationale": "Determinism check",
		}
		first = evaluate_feature3a_lifecycle_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE3A_POLICY_V1",
			decision_record=seed["decision"].name,
			lifecycle_context=context,
		)
		second = evaluate_feature3a_lifecycle_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE3A_POLICY_V1",
			decision_record=seed["decision"].name,
			lifecycle_context=context,
		)
		self.assertEqual([item.as_dict() for item in first], [item.as_dict() for item in second])

	def test_report_executes_for_governance_roles(self):
		seed = self.seed_dataset()
		for user in (self.owner_user, self.sponsor_user, self.operations_user, self.system_manager_user):
			payload = run_query_report(
				report_name="Feature 3A Follow-Through Lifecycle Governance Review",
				user=user,
				filters={
					"lighthouse_workflow_charter": seed["charter"].name,
					"decision_record": seed["decision"].name,
					"review_window_start": add_days(today(), -30),
					"review_window_end": add_days(today(), 30),
					"policy_version": "FEATURE3A_POLICY_V1",
				},
			)
			self.assertIn("result", payload)
			self.assertTrue(payload["result"])

	def test_permission_enforcement_for_unprivileged_user(self):
		seed = self.seed_dataset()
		frappe.set_user(self.unprivileged_user)
		self.assertRaises(
			frappe.PermissionError,
			run_query_report,
			report_name="Feature 3A Follow-Through Lifecycle Governance Review",
			filters={
				"lighthouse_workflow_charter": seed["charter"].name,
				"decision_record": seed["decision"].name,
				"review_window_start": add_days(today(), -30),
				"review_window_end": add_days(today(), 30),
				"policy_version": "FEATURE3A_POLICY_V1",
			},
		)

	def test_baseline_records_not_mutated(self):
		seed = self.seed_dataset()
		decision_before = frappe.get_value(
			"Decision Record",
			seed["decision"].name,
			["approval_state", "modified"],
			as_dict=True,
		)
		dependency_before = frappe.get_value(
			"Dependency Exception Record",
			seed["dependency"].name,
			["dependency_status", "modified"],
			as_dict=True,
		)
		attribution_before = frappe.get_value(
			"Attribution Case",
			seed["attribution"].name,
			["confidence_score", "modified"],
			as_dict=True,
		)

		evaluate_feature3a_lifecycle_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE3A_POLICY_V1",
			decision_record=seed["decision"].name,
			lifecycle_context={
				"current_state": "In Progress",
				"requested_action": "Escalate",
				"manual_escalation_requested": 1,
			},
		)

		decision_after = frappe.get_value(
			"Decision Record",
			seed["decision"].name,
			["approval_state", "modified"],
			as_dict=True,
		)
		dependency_after = frappe.get_value(
			"Dependency Exception Record",
			seed["dependency"].name,
			["dependency_status", "modified"],
			as_dict=True,
		)
		attribution_after = frappe.get_value(
			"Attribution Case",
			seed["attribution"].name,
			["confidence_score", "modified"],
			as_dict=True,
		)

		self.assertEqual(decision_before.approval_state, decision_after.approval_state)
		self.assertEqual(dependency_before.dependency_status, dependency_after.dependency_status)
		self.assertEqual(attribution_before.confidence_score, attribution_after.confidence_score)

	def test_feature2_regression_safety(self):
		from enterprise_intelligence_platform.feature2_follow_through_orchestration import (
			evaluate_feature2_prioritization,
		)

		self.ensure_feature2_report_configuration()
		seed = self.seed_dataset()
		items = evaluate_feature2_prioritization(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE2_POLICY_V1",
		)
		self.assertIsInstance(items, tuple)

	def test_actor_trace_audit_evidence_is_recorded(self):
		seed = self.seed_dataset()
		with patch("enterprise_intelligence_platform.feature3a_follow_through_lifecycle_orchestration.frappe.logger") as logger_mock:
			evaluate_feature3a_lifecycle_governance(
				lighthouse_workflow_charter=seed["charter"].name,
				review_window_start=add_days(today(), -30),
				review_window_end=add_days(today(), 30),
				policy_version="FEATURE3A_POLICY_V1",
				decision_record=seed["decision"].name,
				lifecycle_context={
					"current_state": "Identified",
					"requested_action": "Prioritize",
				},
			)
			self.assertTrue(logger_mock.called)
			self.assertTrue(logger_mock.return_value.info.called)
			payload = logger_mock.return_value.info.call_args[0][0]
			self.assertEqual(payload["event"], "feature3a_lifecycle_governance_review_executed")
			self.assertEqual(payload["source_charter"], seed["charter"].name)
