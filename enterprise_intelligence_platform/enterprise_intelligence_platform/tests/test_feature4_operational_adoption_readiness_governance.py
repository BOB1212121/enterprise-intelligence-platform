from unittest.mock import patch

import frappe
from frappe.desk.query_report import run as run_query_report
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, random_string, today

from enterprise_intelligence_platform.feature4_operational_adoption_readiness_governance import (
	DEFER,
	GO,
	NO_GO,
	evaluate_feature4_readiness_governance,
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


class TestFeature4OperationalAdoptionReadinessGovernance(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		setup_s1_f1()
		setup_s1_f2()
		setup_s1_f3()
		setup_s2_f2()
		cls.ensure_feature4_report_configuration()

		cls.owner_user = cls.make_user_with_role("eip_feature4_owner@example.com", "EIP Workflow Owner")
		cls.sponsor_user = cls.make_user_with_role("eip_feature4_sponsor@example.com", "EIP Executive Sponsor")
		cls.operations_user = cls.make_user_with_role(
			"eip_feature4_operations@example.com", "EIP Operations Manager"
		)
		cls.system_manager_user = cls.make_user_with_role("eip_feature4_system@example.com", "System Manager")
		cls.unprivileged_user = cls.make_base_user("eip_feature4_unprivileged@example.com")

	@classmethod
	def ensure_feature4_report_configuration(cls):
		report_name = "Feature 4 Operational Adoption Readiness Governance Review"
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
				"workflow_name": f"Feature 4 Charter {random_string(8)}",
				"business_objective": "Operational adoption readiness governance.",
				"in_scope_definition": "Feature 4 readiness governance-only scope.",
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
				"decision_title": f"Feature 4 Decision {random_string(8)}",
				"lighthouse_workflow_charter": charter_name,
				"accountable_owner": self.owner_user,
				"executive_sponsor": self.sponsor_user,
				"decision_type": "Operational",
				"decision_criticality": "High",
				"proposal_date": add_days(today(), -5),
				"target_decision_date": add_days(today(), 3),
				"business_decision_summary": "Feature 4 readiness governance context.",
				"tradeoff_summary": "Tradeoff context.",
				"assumptions": [
					{
						"assumption_text": "Readiness evidence remains available.",
						"confidence_score": 0.8,
						"falsifiability_note": "Invalidate if readiness evidence is unavailable.",
					}
				],
			}
		).insert(ignore_permissions=True)

	def seed_dataset(self):
		charter = self.make_charter_doc().insert(ignore_permissions=True)
		decision = self.make_decision_doc(charter.name)
		return {"charter": charter, "decision": decision}

	def make_evidence_package(
		self,
		*,
		trigger_status="not_triggered",
		adr_status="not_required",
		proposed_outcome="GO",
		rollback_value=None,
		incident_value=None,
		owner_approval="Approved",
		sponsor_approval="Approved",
		system_approval="Approved",
		operations_approval="Approved",
	):
		if rollback_value is None:
			rollback_value = "Validated rollback plan for readiness window"
		if incident_value is None:
			incident_value = "Validated incident response runbook for readiness window"
		return {
			"readiness_package_id": f"F4-RPK-{random_string(8)}",
			"policy_version": "FEATURE4_POLICY_V1",
			"target_readiness_window_start": add_days(today(), -7),
			"target_readiness_window_end": add_days(today(), 7),
			"feature_scope_declaration": "Sprint 3 Feature 4 only",
			"additive_only_conformance_declaration": "Confirmed",
			"baseline_contract_preservation_declaration": "Confirmed",
			"feature_1_contract_preservation_declaration": "Confirmed",
			"feature_2_contract_preservation_declaration": "Confirmed",
			"feature_3a_contract_preservation_declaration": "Confirmed",
			"feature_3b_contract_preservation_declaration": "Confirmed",
			"baseline_change_trigger_status": trigger_status,
			"adr_route_status": adr_status,
			"rollback_readiness_reference": rollback_value,
			"incident_response_readiness_reference": incident_value,
			"regression_coverage_declaration": "Covers frozen baseline and Feature 1, Feature 2, Feature 3A, Feature 3B contract non-interference.",
			"security_access_control_declaration": "Confirmed",
			"traceability_evidence_references": ["F4-EVID-001", "F4-EVID-002"],
			"approver_decision_workflow_owner": owner_approval,
			"approver_decision_executive_sponsor": sponsor_approval,
			"approver_decision_system_manager": system_approval,
			"approver_decision_operations_manager": operations_approval,
			"decision_timestamp": f"{today()}T00:00:00",
			"decision_actor": self.owner_user,
			"proposed_readiness_outcome": proposed_outcome,
		}

	def test_go_outcome_and_implementation_authorized_is_zero(self):
		seed = self.seed_dataset()
		items = evaluate_feature4_readiness_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE4_POLICY_V1",
			decision_record=seed["decision"].name,
			readiness_context={"evidence_package": self.make_evidence_package()},
		)
		self.assertEqual(items[0].readiness_outcome, GO)
		self.assertEqual(items[0].implementation_authorized, 0)
		self.assertEqual(items[0].gate_sequence_passed, 1)

	def test_missing_mandatory_field_results_in_no_go(self):
		seed = self.seed_dataset()
		package = self.make_evidence_package()
		package.pop("decision_actor")
		items = evaluate_feature4_readiness_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE4_POLICY_V1",
			decision_record=seed["decision"].name,
			readiness_context={"evidence_package": package},
		)
		self.assertEqual(items[0].readiness_outcome, NO_GO)
		self.assertEqual(items[0].rg_001_evidence_completeness_pass, 0)

	def test_baseline_trigger_unresolved_results_in_no_go(self):
		seed = self.seed_dataset()
		items = evaluate_feature4_readiness_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE4_POLICY_V1",
			decision_record=seed["decision"].name,
			readiness_context={
				"evidence_package": self.make_evidence_package(
					trigger_status="triggered_unresolved",
					adr_status="required_not_routed",
				),
			},
		)
		self.assertEqual(items[0].readiness_outcome, NO_GO)
		self.assertEqual(items[0].adr_route_required, 1)

	def test_baseline_trigger_routed_results_in_defer(self):
		seed = self.seed_dataset()
		items = evaluate_feature4_readiness_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE4_POLICY_V1",
			decision_record=seed["decision"].name,
			readiness_context={
				"evidence_package": self.make_evidence_package(
					trigger_status="triggered_routed",
					adr_status="required_routed",
					proposed_outcome="DEFER",
				),
			},
		)
		self.assertEqual(items[0].readiness_outcome, DEFER)
		self.assertEqual(items[0].adr_route_required, 1)

	def test_mutation_detection_forces_no_go_and_adr_route(self):
		seed = self.seed_dataset()
		items = evaluate_feature4_readiness_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE4_POLICY_V1",
			decision_record=seed["decision"].name,
			readiness_context={
				"evidence_package": self.make_evidence_package(),
				"mutation_indicators": {
					"modifies_workflow_semantics": 1,
				},
			},
		)
		self.assertEqual(items[0].readiness_outcome, NO_GO)
		self.assertEqual(items[0].adr_route_required, 1)
		self.assertEqual(items[0].rg_002_additive_conformance_pass, 0)

	def test_critical_safety_failure_is_no_go(self):
		seed = self.seed_dataset()
		items = evaluate_feature4_readiness_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE4_POLICY_V1",
			decision_record=seed["decision"].name,
			readiness_context={
				"evidence_package": self.make_evidence_package(rollback_value="Not validated rollback plan"),
			},
		)
		self.assertEqual(items[0].readiness_outcome, NO_GO)
		self.assertEqual(items[0].rg_005_rollback_readiness_pass, 0)

	def test_deterministic_behavior(self):
		seed = self.seed_dataset()
		context = {
			"evidence_package": self.make_evidence_package(),
			"governance_rationale": "Determinism check",
		}
		first = evaluate_feature4_readiness_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE4_POLICY_V1",
			decision_record=seed["decision"].name,
			readiness_context=context,
		)
		second = evaluate_feature4_readiness_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE4_POLICY_V1",
			decision_record=seed["decision"].name,
			readiness_context=context,
		)
		self.assertEqual([item.as_dict() for item in first], [item.as_dict() for item in second])

	def test_report_invalid_context_json_fails(self):
		seed = self.seed_dataset()
		self.assertRaises(
			frappe.ValidationError,
			run_query_report,
			report_name="Feature 4 Operational Adoption Readiness Governance Review",
			user=self.owner_user,
			filters={
				"lighthouse_workflow_charter": seed["charter"].name,
				"decision_record": seed["decision"].name,
				"review_window_start": add_days(today(), -30),
				"review_window_end": add_days(today(), 30),
				"policy_version": "FEATURE4_POLICY_V1",
				"readiness_context_json": "{not-valid-json}",
			},
		)

	def test_report_executes_for_governance_roles(self):
		seed = self.seed_dataset()
		context = {"evidence_package": self.make_evidence_package()}
		for user in (self.owner_user, self.sponsor_user, self.operations_user, self.system_manager_user):
			payload = run_query_report(
				report_name="Feature 4 Operational Adoption Readiness Governance Review",
				user=user,
				filters={
					"lighthouse_workflow_charter": seed["charter"].name,
					"decision_record": seed["decision"].name,
					"review_window_start": add_days(today(), -30),
					"review_window_end": add_days(today(), 30),
					"policy_version": "FEATURE4_POLICY_V1",
					"readiness_context_json": frappe.as_json(context),
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
			report_name="Feature 4 Operational Adoption Readiness Governance Review",
			filters={
				"lighthouse_workflow_charter": seed["charter"].name,
				"decision_record": seed["decision"].name,
				"review_window_start": add_days(today(), -30),
				"review_window_end": add_days(today(), 30),
				"policy_version": "FEATURE4_POLICY_V1",
			},
		)

	def test_actor_trace_audit_evidence_is_recorded(self):
		seed = self.seed_dataset()
		with patch("enterprise_intelligence_platform.feature4_operational_adoption_readiness_governance.frappe.logger") as logger_mock:
			evaluate_feature4_readiness_governance(
				lighthouse_workflow_charter=seed["charter"].name,
				review_window_start=add_days(today(), -30),
				review_window_end=add_days(today(), 30),
				policy_version="FEATURE4_POLICY_V1",
				decision_record=seed["decision"].name,
				readiness_context={"evidence_package": self.make_evidence_package()},
			)
			self.assertTrue(logger_mock.called)
			self.assertTrue(logger_mock.return_value.info.called)
			payload = logger_mock.return_value.info.call_args[0][0]
			self.assertEqual(payload["event"], "feature4_readiness_governance_review_executed")
			self.assertEqual(payload["source_charter"], seed["charter"].name)

	def test_baseline_records_not_mutated(self):
		seed = self.seed_dataset()
		decision_before = frappe.get_value(
			"Decision Record",
			seed["decision"].name,
			["approval_state", "modified"],
			as_dict=True,
		)

		evaluate_feature4_readiness_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE4_POLICY_V1",
			decision_record=seed["decision"].name,
			readiness_context={"evidence_package": self.make_evidence_package()},
		)

		decision_after = frappe.get_value(
			"Decision Record",
			seed["decision"].name,
			["approval_state", "modified"],
			as_dict=True,
		)
		self.assertEqual(decision_before.approval_state, decision_after.approval_state)
