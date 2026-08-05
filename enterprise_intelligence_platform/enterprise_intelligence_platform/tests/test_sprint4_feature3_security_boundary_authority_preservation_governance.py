from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, random_string, today

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
from enterprise_intelligence_platform.sprint4_feature3_security_boundary_authority_preservation_governance import (
	DEFER,
	GO,
	NO_GO,
	evaluate_sprint4_feature3_security_boundary_authority_preservation_governance,
)


class TestSprint4Feature3SecurityBoundaryAuthorityPreservationGovernance(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		setup_s1_f1()
		setup_s1_f2()
		setup_s1_f3()
		setup_s2_f2()

		cls.owner_user = cls.make_user_with_role("s4f3_owner@example.com", "EIP Workflow Owner")
		cls.sponsor_user = cls.make_user_with_role("s4f3_sponsor@example.com", "EIP Executive Sponsor")
		cls.operations_user = cls.make_user_with_role("s4f3_operations@example.com", "EIP Operations Manager")
		cls.system_manager_user = cls.make_user_with_role("s4f3_system@example.com", "System Manager")
		cls.unprivileged_user = cls.make_base_user("s4f3_unprivileged@example.com")

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
				"workflow_name": f"S4F3 Charter {random_string(8)}",
				"business_objective": "Sprint 4 Feature 3 security boundary and authority preservation governance.",
				"in_scope_definition": "Sprint 4 Feature 3 planning-only governance scope.",
				"accountable_owner": self.owner_user,
				"executive_sponsor": self.sponsor_user,
				"operating_cadence": "Weekly",
				"baseline_start_date": "2026-08-01",
				"baseline_end_date": "2026-09-30",
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
				"decision_title": f"S4F3 Decision {random_string(8)}",
				"lighthouse_workflow_charter": charter_name,
				"accountable_owner": self.owner_user,
				"executive_sponsor": self.sponsor_user,
				"decision_type": "Operational",
				"decision_criticality": "High",
				"proposal_date": add_days(today(), -5),
				"target_decision_date": add_days(today(), 3),
				"business_decision_summary": "Sprint 4 Feature 3 governance context.",
				"tradeoff_summary": "Tradeoff context.",
				"assumptions": [
					{
						"assumption_text": "Evidence remains available.",
						"confidence_score": 0.8,
						"falsifiability_note": "Invalidate if evidence becomes unavailable.",
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
		defer_blocker_type=None,
		defer_blocker_reference=None,
		contract_statement=None,
		operational_safety_record=None,
	):
		if contract_statement is None:
			contract_statement = (
				"Confirmed non-interference with Feature 1, Feature 2, Feature 3A, Feature 3B, Feature 4, "
				"Sprint 4 Feature 1, Sprint 4 Feature 2, and frozen v0.2.0-baseline."
			)
		if operational_safety_record is None:
			operational_safety_record = {
				"rollback_readiness": "Confirmed",
				"incident_response_readiness": "Confirmed",
				"recovery_readiness": "Confirmed",
				"operational_verification_readiness": "Confirmed",
				"monitoring_observability_readiness": "Confirmed",
			}

		package = {
			"scope_declaration": "Sprint 4 Feature 3 security boundary and authority preservation governance only",
			"baseline_preservation_statement": "Confirmed",
			"additive_only_statement": "Confirmed",
			"contract_preservation_statement": contract_statement,
			"gate_assessment_record": "Gate 1 pass; Gate 2 pass; Gate 3 pass; Gate 4 pass; Gate 5 pass",
			"approval_authority_record": (
				"EIP Workflow Owner=Approved; EIP Executive Sponsor=Approved; "
				"System Manager=Approved; EIP Operations Manager=Approved"
			),
			"security_boundary_confirmation": "Confirmed",
			"operational_safety_record": operational_safety_record,
			"traceability_audit_record": "Actor/time/context captured with evidence refs",
			"validation_replay_record": "FR/NFR/AC replay matrix complete",
			"baseline_change_trigger_status": trigger_status,
		}
		if defer_blocker_type is not None:
			package["defer_blocker_type"] = defer_blocker_type
		if defer_blocker_reference is not None:
			package["defer_blocker_reference"] = defer_blocker_reference
		return package

	def test_go_outcome_and_implementation_authorized_is_zero(self):
		seed = self.seed_dataset()
		items = evaluate_sprint4_feature3_security_boundary_authority_preservation_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="S4F3_POLICY_V1",
			decision_record=seed["decision"].name,
			governance_context={"evidence_package": self.make_evidence_package()},
		)
		self.assertEqual(items[0].readiness_outcome, GO)
		self.assertEqual(items[0].implementation_authorized, 0)
		self.assertEqual(items[0].gate_sequence_passed, 1)

	def test_missing_mandatory_field_results_in_no_go(self):
		seed = self.seed_dataset()
		package = self.make_evidence_package()
		package.pop("scope_declaration")
		items = evaluate_sprint4_feature3_security_boundary_authority_preservation_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="S4F3_POLICY_V1",
			decision_record=seed["decision"].name,
			governance_context={"evidence_package": package},
		)
		self.assertEqual(items[0].readiness_outcome, NO_GO)
		self.assertEqual(items[0].rg_001_evidence_completeness_pass, 0)

	def test_non_reviewable_mandatory_evidence_results_in_no_go(self):
		seed = self.seed_dataset()
		package = self.make_evidence_package()
		package["security_boundary_confirmation"] = ""
		items = evaluate_sprint4_feature3_security_boundary_authority_preservation_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="S4F3_POLICY_V1",
			decision_record=seed["decision"].name,
			governance_context={"evidence_package": package},
		)
		self.assertEqual(items[0].readiness_outcome, NO_GO)

	def test_defer_allowed_for_external_dependency_when_all_conditions_pass(self):
		seed = self.seed_dataset()
		package = self.make_evidence_package(
			defer_blocker_type="external_dependency",
			defer_blocker_reference="S4F3-EXT-DEP-001",
		)
		items = evaluate_sprint4_feature3_security_boundary_authority_preservation_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="S4F3_POLICY_V1",
			decision_record=seed["decision"].name,
			governance_context={"evidence_package": package},
		)
		self.assertEqual(items[0].readiness_outcome, DEFER)

	def test_invalid_defer_blocker_type_is_no_go(self):
		seed = self.seed_dataset()
		package = self.make_evidence_package(
			defer_blocker_type="vendor_delay",
			defer_blocker_reference="S4F3-DEP-001",
		)
		items = evaluate_sprint4_feature3_security_boundary_authority_preservation_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="S4F3_POLICY_V1",
			decision_record=seed["decision"].name,
			governance_context={"evidence_package": package},
		)
		self.assertEqual(items[0].readiness_outcome, NO_GO)

	def test_missing_defer_blocker_reference_is_no_go(self):
		seed = self.seed_dataset()
		package = self.make_evidence_package(defer_blocker_type="scheduled_governance_activity")
		items = evaluate_sprint4_feature3_security_boundary_authority_preservation_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="S4F3_POLICY_V1",
			decision_record=seed["decision"].name,
			governance_context={"evidence_package": package},
		)
		self.assertEqual(items[0].readiness_outcome, NO_GO)

	def test_non_reviewable_defer_blocker_reference_is_no_go(self):
		seed = self.seed_dataset()
		package = self.make_evidence_package(
			defer_blocker_type="scheduled_governance_activity",
			defer_blocker_reference="",
		)
		items = evaluate_sprint4_feature3_security_boundary_authority_preservation_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="S4F3_POLICY_V1",
			decision_record=seed["decision"].name,
			governance_context={"evidence_package": package},
		)
		self.assertEqual(items[0].readiness_outcome, NO_GO)

	def test_missing_defer_blocker_type_with_reference_is_no_go(self):
		seed = self.seed_dataset()
		package = self.make_evidence_package(defer_blocker_reference="S4F3-REF-ONLY")
		items = evaluate_sprint4_feature3_security_boundary_authority_preservation_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="S4F3_POLICY_V1",
			decision_record=seed["decision"].name,
			governance_context={"evidence_package": package},
		)
		self.assertEqual(items[0].readiness_outcome, NO_GO)

	def test_unresolved_trigger_is_no_go_and_requires_adr_route(self):
		seed = self.seed_dataset()
		package = self.make_evidence_package(trigger_status="triggered_unresolved")
		items = evaluate_sprint4_feature3_security_boundary_authority_preservation_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="S4F3_POLICY_V1",
			decision_record=seed["decision"].name,
			governance_context={"evidence_package": package},
		)
		self.assertEqual(items[0].readiness_outcome, NO_GO)
		self.assertEqual(items[0].adr_route_required, 1)

	def test_mutation_indicator_forces_no_go_and_adr_route(self):
		seed = self.seed_dataset()
		items = evaluate_sprint4_feature3_security_boundary_authority_preservation_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="S4F3_POLICY_V1",
			decision_record=seed["decision"].name,
			governance_context={
				"evidence_package": self.make_evidence_package(),
				"mutation_indicators": {"changes_permission_authority": 1},
			},
		)
		self.assertEqual(items[0].readiness_outcome, NO_GO)
		self.assertEqual(items[0].adr_route_required, 1)

	def test_contract_preservation_statement_missing_required_markers_is_no_go(self):
		seed = self.seed_dataset()
		package = self.make_evidence_package(contract_statement="Confirmed feature preservation")
		items = evaluate_sprint4_feature3_security_boundary_authority_preservation_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="S4F3_POLICY_V1",
			decision_record=seed["decision"].name,
			governance_context={"evidence_package": package},
		)
		self.assertEqual(items[0].readiness_outcome, NO_GO)
		self.assertEqual(items[0].rg_002_additive_conformance_pass, 0)

	def test_gate_3_objective_validation_missing_replay_record_is_no_go(self):
		seed = self.seed_dataset()
		package = self.make_evidence_package()
		package.pop("validation_replay_record")
		items = evaluate_sprint4_feature3_security_boundary_authority_preservation_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="S4F3_POLICY_V1",
			decision_record=seed["decision"].name,
			governance_context={"evidence_package": package},
		)
		self.assertEqual(items[0].readiness_outcome, NO_GO)
		self.assertEqual(items[0].gate_3_pass, 0)

	def test_operational_safety_criterion_failures_result_in_no_go(self):
		seed = self.seed_dataset()
		package = self.make_evidence_package(
			operational_safety_record={
				"rollback_readiness": "Confirmed",
				"incident_response_readiness": "Confirmed",
				"recovery_readiness": "Confirmed",
				"operational_verification_readiness": "Confirmed",
				"monitoring_observability_readiness": "",
			}
		)
		items = evaluate_sprint4_feature3_security_boundary_authority_preservation_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="S4F3_POLICY_V1",
			decision_record=seed["decision"].name,
			governance_context={"evidence_package": package},
		)
		self.assertEqual(items[0].readiness_outcome, NO_GO)
		self.assertEqual(items[0].rg_009_monitoring_observability_pass, 0)

	def test_approval_authority_rejection_results_in_no_go(self):
		seed = self.seed_dataset()
		package = self.make_evidence_package()
		package["approval_authority_record"] = (
			"EIP Workflow Owner=Approved; EIP Executive Sponsor=Approved; "
			"System Manager=Rejected; EIP Operations Manager=Approved"
		)
		items = evaluate_sprint4_feature3_security_boundary_authority_preservation_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="S4F3_POLICY_V1",
			decision_record=seed["decision"].name,
			governance_context={"evidence_package": package},
		)
		self.assertEqual(items[0].readiness_outcome, NO_GO)
		self.assertEqual(items[0].rg_004_mandatory_approvals_pass, 0)

	def test_deterministic_behavior(self):
		seed = self.seed_dataset()
		context = {
			"evidence_package": self.make_evidence_package(),
			"governance_rationale": "Determinism check",
		}
		first = evaluate_sprint4_feature3_security_boundary_authority_preservation_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="S4F3_POLICY_V1",
			decision_record=seed["decision"].name,
			governance_context=context,
		)
		second = evaluate_sprint4_feature3_security_boundary_authority_preservation_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="S4F3_POLICY_V1",
			decision_record=seed["decision"].name,
			governance_context=context,
		)
		self.assertEqual([item.as_dict() for item in first], [item.as_dict() for item in second])

	def test_permission_enforcement_for_unprivileged_user(self):
		seed = self.seed_dataset()
		frappe.set_user(self.unprivileged_user)
		self.assertRaises(
			frappe.PermissionError,
			evaluate_sprint4_feature3_security_boundary_authority_preservation_governance,
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="S4F3_POLICY_V1",
			decision_record=seed["decision"].name,
			governance_context={"evidence_package": self.make_evidence_package()},
		)

	def test_actor_trace_audit_evidence_is_recorded(self):
		seed = self.seed_dataset()
		with patch(
			"enterprise_intelligence_platform.sprint4_feature3_security_boundary_authority_preservation_governance.frappe.logger"
		) as logger_mock:
			evaluate_sprint4_feature3_security_boundary_authority_preservation_governance(
				lighthouse_workflow_charter=seed["charter"].name,
				review_window_start=add_days(today(), -30),
				review_window_end=add_days(today(), 30),
				policy_version="S4F3_POLICY_V1",
				decision_record=seed["decision"].name,
				governance_context={"evidence_package": self.make_evidence_package()},
			)
			self.assertTrue(logger_mock.called)
			payload = logger_mock.return_value.info.call_args[0][0]
			self.assertEqual(
				payload["event"],
				"sprint4_feature3_security_boundary_authority_preservation_governance_review_executed",
			)
			self.assertEqual(payload["source_charter"], seed["charter"].name)

	def test_baseline_records_not_mutated(self):
		seed = self.seed_dataset()
		decision_before = frappe.get_value(
			"Decision Record",
			seed["decision"].name,
			["approval_state", "modified"],
			as_dict=True,
		)

		evaluate_sprint4_feature3_security_boundary_authority_preservation_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="S4F3_POLICY_V1",
			decision_record=seed["decision"].name,
			governance_context={"evidence_package": self.make_evidence_package()},
		)

		decision_after = frappe.get_value(
			"Decision Record",
			seed["decision"].name,
			["approval_state", "modified"],
			as_dict=True,
		)
		self.assertEqual(decision_before.approval_state, decision_after.approval_state)
