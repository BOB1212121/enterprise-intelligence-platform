from unittest.mock import patch

import frappe
from frappe.desk.query_report import run as run_query_report
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, random_string, today

from enterprise_intelligence_platform.feature3b_conditional_baseline_change_governance import (
	OUTCOME_APPROVED_FUTURE_TRACK,
	OUTCOME_CONTINUE_BLOCKED,
	OUTCOME_NOT_TRIGGERED,
	OUTCOME_REJECTED,
	evaluate_feature3b_baseline_change_governance,
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


class TestFeature3BConditionalBaselineChangeGovernance(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		setup_s1_f1()
		setup_s1_f2()
		setup_s1_f3()
		setup_s2_f2()
		cls.ensure_feature3b_report_configuration()

		cls.owner_user = cls.make_user_with_role("eip_feature3b_owner@example.com", "EIP Workflow Owner")
		cls.sponsor_user = cls.make_user_with_role("eip_feature3b_sponsor@example.com", "EIP Executive Sponsor")
		cls.operations_user = cls.make_user_with_role(
			"eip_feature3b_operations@example.com", "EIP Operations Manager"
		)
		cls.system_manager_user = cls.make_user_with_role("eip_feature3b_system@example.com", "System Manager")
		cls.unprivileged_user = cls.make_base_user("eip_feature3b_unprivileged@example.com")

	@classmethod
	def ensure_feature3b_report_configuration(cls):
		report_name = "Feature 3B Baseline Change Governance Review"
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
				"workflow_name": f"Feature 3B Charter {random_string(8)}",
				"business_objective": "Conditional baseline-change governance planning readiness.",
				"in_scope_definition": "Feature 3B governance-only baseline-change track.",
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
				"decision_title": f"Feature 3B Decision {random_string(8)}",
				"lighthouse_workflow_charter": charter_name,
				"accountable_owner": self.owner_user,
				"executive_sponsor": self.sponsor_user,
				"decision_type": "Operational",
				"decision_criticality": "High",
				"proposal_date": add_days(today(), -5),
				"target_decision_date": add_days(today(), 3),
				"business_decision_summary": "Feature 3B baseline-change governance context.",
				"tradeoff_summary": "Tradeoff context.",
				"assumptions": [
					{
						"assumption_text": "Governance evidence remains available.",
						"confidence_score": 0.8,
						"falsifiability_note": "Invalidate if baseline references are unavailable.",
					}
				],
			}
		).insert(ignore_permissions=True)

	def seed_dataset(self):
		charter = self.make_charter_doc().insert(ignore_permissions=True)
		decision = self.make_decision_doc(charter.name)
		return {"charter": charter, "decision": decision}

	def make_adr_evidence(self):
		return {
			"trigger_identifiers": ["BC-001"],
			"trigger_description": "Workflow semantics mutation request detected.",
			"triggering_feature_and_capability": "Feature 3B / Baseline Change Governance",
			"affected_baseline_artifacts": ["Decision Record Workflow"],
			"impact_assessment": "Would alter frozen baseline semantics.",
			"alternatives_considered": ["Keep additive model", "Defer to ADR future track"],
			"baseline_change_justification": "Change cannot remain additive.",
			"risk_assessment": "High governance risk without ADR route.",
			"architecture_impact_assessment": "Requires architecture checkpoint.",
			"baseline_compatibility_assessment": "Not baseline-compatible without ADR.",
			"traceability_references": ["SPRINT_3_FEATURE_3B_IMPLEMENTATION_SPECIFICATION"],
			"requested_disposition": "accept_future_baseline_change_path",
			"decision_owners": [self.owner_user, self.sponsor_user],
		}

	def make_approver_decisions(self, *, include_reentry_approver=True):
		decisions = {
			"EIP Workflow Owner": 1,
			"EIP Executive Sponsor": 1,
			"System Manager": 1,
			"EIP Operations Manager": 1 if include_reentry_approver else 0,
		}
		return decisions

	def make_stop_declaration(self, *, disposition="Approved for future baseline-change track"):
		return {
			"trigger_identifier": "BC-001",
			"trigger_timestamp": f"{today()}T00:00:00",
			"triggered_feature": "Feature 3B",
			"implementation_stop_reason": "Baseline Change trigger detected",
			"affected_scope": "Requested baseline mutation",
			"responsible_governance_owner": self.owner_user,
			"adr_reference": "ADR-3B-001",
			"current_disposition": disposition,
			"reentry_conditions": "All mandatory approvals and architecture checkpoint approved",
		}

	def test_trigger_detection_sets_stop_and_adr_route(self):
		seed = self.seed_dataset()
		items = evaluate_feature3b_baseline_change_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE3B_POLICY_V1",
			decision_record=seed["decision"].name,
			baseline_change_context={
				"trigger_flags": {"modifies_workflow_semantics": 1},
				"requested_disposition": "continue_blocked",
				"adr_evidence": self.make_adr_evidence(),
				"approver_decisions": self.make_approver_decisions(),
				"architecture_approval_granted": 1,
				"stop_declaration": self.make_stop_declaration(),
			},
		)
		self.assertEqual(items[0].baseline_change_trigger_detected, 1)
		self.assertEqual(items[0].implementation_stop_required, 1)
		self.assertEqual(items[0].adr_route_required, 1)

	def test_no_trigger_results_in_not_triggered_outcome(self):
		seed = self.seed_dataset()
		items = evaluate_feature3b_baseline_change_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE3B_POLICY_V1",
			decision_record=seed["decision"].name,
			baseline_change_context={},
		)
		self.assertEqual(items[0].baseline_change_trigger_detected, 0)
		self.assertEqual(items[0].disposition_outcome, OUTCOME_NOT_TRIGGERED)
		self.assertEqual(items[0].implementation_authorized, 0)

	def test_incomplete_adr_evidence_blocks_initiation(self):
		seed = self.seed_dataset()
		evidence = self.make_adr_evidence()
		evidence.pop("risk_assessment")
		items = evaluate_feature3b_baseline_change_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE3B_POLICY_V1",
			decision_record=seed["decision"].name,
			baseline_change_context={
				"trigger_flags": {"changes_approval_state_semantics": 1},
				"requested_disposition": "accept_future_baseline_change_path",
				"adr_evidence": evidence,
				"approver_decisions": self.make_approver_decisions(),
				"architecture_approval_granted": 1,
				"stop_declaration": self.make_stop_declaration(),
			},
		)
		self.assertEqual(items[0].adr_evidence_complete, 0)
		self.assertEqual(items[0].adr_initiation_blocked, 1)
		self.assertEqual(items[0].disposition_outcome, OUTCOME_CONTINUE_BLOCKED)

	def test_missing_mandatory_disposition_approval_blocks(self):
		seed = self.seed_dataset()
		approvals = self.make_approver_decisions()
		approvals["System Manager"] = 0
		items = evaluate_feature3b_baseline_change_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE3B_POLICY_V1",
			decision_record=seed["decision"].name,
			baseline_change_context={
				"trigger_flags": {"modifies_permission_semantics": 1},
				"requested_disposition": "accept_future_baseline_change_path",
				"adr_evidence": self.make_adr_evidence(),
				"approver_decisions": approvals,
				"architecture_approval_granted": 1,
				"stop_declaration": self.make_stop_declaration(),
			},
		)
		self.assertEqual(items[0].mandatory_disposition_approvals_complete, 0)
		self.assertEqual(items[0].disposition_outcome, OUTCOME_CONTINUE_BLOCKED)

	def test_architecture_checkpoint_not_approved_blocks(self):
		seed = self.seed_dataset()
		items = evaluate_feature3b_baseline_change_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE3B_POLICY_V1",
			decision_record=seed["decision"].name,
			baseline_change_context={
				"trigger_flags": {"alters_ownership_or_source_of_truth": 1},
				"requested_disposition": "accept_future_baseline_change_path",
				"adr_evidence": self.make_adr_evidence(),
				"approver_decisions": self.make_approver_decisions(),
				"architecture_approval_granted": 0,
				"stop_declaration": self.make_stop_declaration(),
			},
		)
		self.assertEqual(items[0].architecture_approval_granted, 0)
		self.assertEqual(items[0].disposition_outcome, OUTCOME_CONTINUE_BLOCKED)

	def test_reject_disposition_path(self):
		seed = self.seed_dataset()
		items = evaluate_feature3b_baseline_change_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE3B_POLICY_V1",
			decision_record=seed["decision"].name,
			baseline_change_context={
				"trigger_flags": {"mutates_approved_feature_contracts": 1},
				"requested_disposition": "reject_baseline_change",
				"adr_evidence": {**self.make_adr_evidence(), "requested_disposition": "reject_baseline_change"},
				"approver_decisions": self.make_approver_decisions(),
				"architecture_approval_granted": 1,
				"stop_declaration": self.make_stop_declaration(disposition="Rejected"),
			},
		)
		self.assertEqual(items[0].disposition_outcome, OUTCOME_REJECTED)
		self.assertEqual(items[0].implementation_authorized, 0)

	def test_approved_future_track_requires_reentry_approver_for_reentry_authorization(self):
		seed = self.seed_dataset()
		items = evaluate_feature3b_baseline_change_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE3B_POLICY_V1",
			decision_record=seed["decision"].name,
			baseline_change_context={
				"trigger_flags": {"changes_immutability_behavior": 1},
				"requested_disposition": "accept_future_baseline_change_path",
				"adr_evidence": self.make_adr_evidence(),
				"approver_decisions": self.make_approver_decisions(include_reentry_approver=True),
				"architecture_approval_granted": 1,
				"stop_declaration": self.make_stop_declaration(),
			},
		)
		self.assertEqual(items[0].disposition_outcome, OUTCOME_APPROVED_FUTURE_TRACK)
		self.assertEqual(items[0].reentry_planning_authorized, 1)
		self.assertEqual(items[0].implementation_authorized, 0)

	def test_incomplete_stop_declaration_forces_continue_blocked(self):
		seed = self.seed_dataset()
		stop = self.make_stop_declaration()
		stop.pop("reentry_conditions")
		items = evaluate_feature3b_baseline_change_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE3B_POLICY_V1",
			decision_record=seed["decision"].name,
			baseline_change_context={
				"trigger_flags": {"introduces_conflicting_duplicate_source_of_truth_persistence": 1},
				"requested_disposition": "accept_future_baseline_change_path",
				"adr_evidence": self.make_adr_evidence(),
				"approver_decisions": self.make_approver_decisions(),
				"architecture_approval_granted": 1,
				"stop_declaration": stop,
			},
		)
		self.assertEqual(items[0].implementation_stop_declaration_complete, 0)
		self.assertEqual(items[0].disposition_outcome, OUTCOME_CONTINUE_BLOCKED)

	def test_deterministic_behavior(self):
		seed = self.seed_dataset()
		context = {
			"trigger_flags": {"modifies_workflow_semantics": 1},
			"requested_disposition": "accept_future_baseline_change_path",
			"adr_evidence": self.make_adr_evidence(),
			"approver_decisions": self.make_approver_decisions(),
			"architecture_approval_granted": 1,
			"stop_declaration": self.make_stop_declaration(),
			"governance_rationale": "Determinism check",
		}
		first = evaluate_feature3b_baseline_change_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE3B_POLICY_V1",
			decision_record=seed["decision"].name,
			baseline_change_context=context,
		)
		second = evaluate_feature3b_baseline_change_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE3B_POLICY_V1",
			decision_record=seed["decision"].name,
			baseline_change_context=context,
		)
		self.assertEqual([item.as_dict() for item in first], [item.as_dict() for item in second])

	def test_report_invalid_context_json_fails(self):
		seed = self.seed_dataset()
		self.assertRaises(
			frappe.ValidationError,
			run_query_report,
			report_name="Feature 3B Baseline Change Governance Review",
			user=self.owner_user,
			filters={
				"lighthouse_workflow_charter": seed["charter"].name,
				"decision_record": seed["decision"].name,
				"review_window_start": add_days(today(), -30),
				"review_window_end": add_days(today(), 30),
				"policy_version": "FEATURE3B_POLICY_V1",
				"baseline_change_context_json": "{not-valid-json}",
			},
		)

	def test_report_executes_for_governance_roles(self):
		seed = self.seed_dataset()
		context = {
			"trigger_flags": {"modifies_workflow_semantics": 1},
			"requested_disposition": "accept_future_baseline_change_path",
			"adr_evidence": self.make_adr_evidence(),
			"approver_decisions": self.make_approver_decisions(),
			"architecture_approval_granted": 1,
			"stop_declaration": self.make_stop_declaration(),
		}
		for user in (self.owner_user, self.sponsor_user, self.operations_user, self.system_manager_user):
			payload = run_query_report(
				report_name="Feature 3B Baseline Change Governance Review",
				user=user,
				filters={
					"lighthouse_workflow_charter": seed["charter"].name,
					"decision_record": seed["decision"].name,
					"review_window_start": add_days(today(), -30),
					"review_window_end": add_days(today(), 30),
					"policy_version": "FEATURE3B_POLICY_V1",
					"baseline_change_context_json": frappe.as_json(context),
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
			report_name="Feature 3B Baseline Change Governance Review",
			filters={
				"lighthouse_workflow_charter": seed["charter"].name,
				"decision_record": seed["decision"].name,
				"review_window_start": add_days(today(), -30),
				"review_window_end": add_days(today(), 30),
				"policy_version": "FEATURE3B_POLICY_V1",
			},
		)

	def test_actor_trace_audit_evidence_is_recorded(self):
		seed = self.seed_dataset()
		with patch("enterprise_intelligence_platform.feature3b_conditional_baseline_change_governance.frappe.logger") as logger_mock:
			evaluate_feature3b_baseline_change_governance(
				lighthouse_workflow_charter=seed["charter"].name,
				review_window_start=add_days(today(), -30),
				review_window_end=add_days(today(), 30),
				policy_version="FEATURE3B_POLICY_V1",
				decision_record=seed["decision"].name,
				baseline_change_context={
					"trigger_flags": {"modifies_workflow_semantics": 1},
					"requested_disposition": "continue_blocked",
					"adr_evidence": self.make_adr_evidence(),
					"approver_decisions": self.make_approver_decisions(),
					"architecture_approval_granted": 1,
					"stop_declaration": self.make_stop_declaration(),
				},
			)
			self.assertTrue(logger_mock.called)
			self.assertTrue(logger_mock.return_value.info.called)
			payload = logger_mock.return_value.info.call_args[0][0]
			self.assertEqual(payload["event"], "feature3b_baseline_change_governance_review_executed")
			self.assertEqual(payload["source_charter"], seed["charter"].name)

	def test_baseline_records_not_mutated(self):
		seed = self.seed_dataset()
		decision_before = frappe.get_value(
			"Decision Record",
			seed["decision"].name,
			["approval_state", "modified"],
			as_dict=True,
		)

		evaluate_feature3b_baseline_change_governance(
			lighthouse_workflow_charter=seed["charter"].name,
			review_window_start=add_days(today(), -30),
			review_window_end=add_days(today(), 30),
			policy_version="FEATURE3B_POLICY_V1",
			decision_record=seed["decision"].name,
			baseline_change_context={
				"trigger_flags": {"modifies_workflow_semantics": 1},
				"requested_disposition": "accept_future_baseline_change_path",
				"adr_evidence": self.make_adr_evidence(),
				"approver_decisions": self.make_approver_decisions(),
				"architecture_approval_granted": 1,
				"stop_declaration": self.make_stop_declaration(),
			},
		)

		decision_after = frappe.get_value(
			"Decision Record",
			seed["decision"].name,
			["approval_state", "modified"],
			as_dict=True,
		)
		self.assertEqual(decision_before.approval_state, decision_after.approval_state)
