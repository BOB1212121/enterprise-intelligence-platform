import frappe
from frappe.desk.query_report import run as run_query_report
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, getdate, random_string, today

from enterprise_intelligence_platform.enterprise_intelligence_platform.report.operational_review_view.operational_review_view import (
	execute,
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


class TestOperationalReviewView(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		setup_s1_f1()
		setup_s1_f2()
		setup_s1_f3()

		cls.owner_user = cls.make_user_with_role("eip_orv_owner@example.com", "EIP Workflow Owner")
		cls.sponsor_user = cls.make_user_with_role("eip_orv_sponsor@example.com", "EIP Executive Sponsor")
		cls.other_owner_user = cls.make_user_with_role("eip_orv_owner2@example.com", "EIP Workflow Owner")
		cls.other_sponsor_user = cls.make_user_with_role(
			"eip_orv_sponsor2@example.com", "EIP Executive Sponsor"
		)
		cls.operations_user = cls.make_user_with_role(
			"eip_orv_operations@example.com", "EIP Operations Manager"
		)
		cls.system_manager_user = cls.make_user_with_role("eip_orv_system@example.com", "System Manager")
		cls.unprivileged_user = cls.make_base_user("eip_orv_unprivileged@example.com")

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
		frappe.get_doc("User", email).add_roles(role)
		return email

	def make_charter(self, owner=None, sponsor=None):
		return frappe.get_doc(
			{
				"doctype": "Lighthouse Workflow Charter",
				"workflow_name": f"ORV Charter {random_string(8)}",
				"business_objective": "Operational review baseline",
				"in_scope_definition": "Operational view scope",
				"accountable_owner": owner or self.owner_user,
				"executive_sponsor": sponsor or self.sponsor_user,
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

	def make_decision(self, charter_name, owner=None, sponsor=None):
		return frappe.get_doc(
			{
				"doctype": "Decision Record",
				"decision_title": f"ORV Decision {random_string(8)}",
				"lighthouse_workflow_charter": charter_name,
				"accountable_owner": owner or self.owner_user,
				"executive_sponsor": sponsor or self.sponsor_user,
				"decision_type": "Operational",
				"decision_criticality": "Medium",
				"proposal_date": "2026-07-15",
				"target_decision_date": "2026-07-20",
				"business_decision_summary": "Operational decision summary",
				"tradeoff_summary": "Tradeoff summary",
				"assumptions": [
					{
						"assumption_text": f"Assumption {random_string(8)}",
						"confidence_score": 0.8,
						"falsifiability_note": "Falsify on mismatch",
					}
				],
			}
		).insert(ignore_permissions=True)

	def make_dependency(
		self,
		decision,
		* ,
		title_suffix,
		owner=None,
		sponsor=None,
		approval_state="Draft",
		dependency_status="Open",
		dependency_criticality="High",
		exception_required=1,
		target_resolution_date=None,
		exception_expiry_date=None,
	):
		target_resolution_date = target_resolution_date or add_days(today(), 7)
		exception_expiry_date = exception_expiry_date or add_days(today(), 14)
		resolution_note = "Resolved during test fixture setup." if dependency_status == "Resolved" else ""
		doc = frappe.get_doc(
			{
				"doctype": "Dependency Exception Record",
				"dependency_title": f"ORV Dependency {title_suffix}",
				"decision_record": decision.name,
				"lighthouse_workflow_charter": decision.lighthouse_workflow_charter,
				"accountable_owner": owner or self.owner_user,
				"executive_sponsor": sponsor or self.sponsor_user,
				"dependency_type": "System",
				"dependency_criticality": dependency_criticality,
				"declaration_date": add_days(target_resolution_date, -3),
				"target_resolution_date": target_resolution_date,
				"dependency_status": dependency_status,
				"resolution_note": resolution_note,
				"dependency_description": "Dependency detail",
				"impact_summary": "Impact detail",
				"mitigation_plan": "Mitigation detail",
				"exception_required": exception_required,
				"exception_owner": owner or self.owner_user,
				"exception_reason": "Reason",
				"exception_expiry_date": exception_expiry_date,
				"remediation_intent": "Intent",
			}
		).insert(ignore_permissions=True)
		if approval_state == "Draft":
			return doc

		if approval_state == "Submitted for Approval":
			doc.approval_state = approval_state
			doc.save(ignore_permissions=True)
			return doc

		raise ValueError(f"Unsupported approval_state fixture value: {approval_state}")
		return doc

	def seed_dataset(self):
		charter_a = self.make_charter(owner=self.owner_user, sponsor=self.sponsor_user)
		charter_b = self.make_charter(owner=self.other_owner_user, sponsor=self.other_sponsor_user)

		decision_a = self.make_decision(charter_a.name, owner=self.owner_user, sponsor=self.sponsor_user)
		decision_b = self.make_decision(
			charter_b.name, owner=self.other_owner_user, sponsor=self.other_sponsor_user
		)

		overdue_date = add_days(today(), -2)
		future_date = add_days(today(), 5)

		dep_a1 = self.make_dependency(
			decision_a,
			title_suffix="A1",
			approval_state="Submitted for Approval",
			dependency_status="Open",
			dependency_criticality="Critical",
			exception_required=1,
			target_resolution_date=overdue_date,
		)
		dep_a2 = self.make_dependency(
			decision_a,
			title_suffix="A2",
			approval_state="Draft",
			dependency_status="At Risk",
			dependency_criticality="High",
			exception_required=1,
			target_resolution_date=future_date,
		)
		dep_a3 = self.make_dependency(
			decision_a,
			title_suffix="A3",
			approval_state="Draft",
			dependency_status="Resolved",
			dependency_criticality="Medium",
			exception_required=1,
			target_resolution_date=future_date,
		)
		dep_b1 = self.make_dependency(
			decision_b,
			title_suffix="B1",
			owner=self.other_owner_user,
			sponsor=self.other_sponsor_user,
			approval_state="Draft",
			dependency_status="Open",
			dependency_criticality="Low",
			exception_required=0,
			target_resolution_date=add_days(today(), 9),
		)

		return {
			"charter_a": charter_a,
			"charter_b": charter_b,
			"decision_a": decision_a,
			"decision_b": decision_b,
			"dep_a1": dep_a1,
			"dep_a2": dep_a2,
			"dep_a3": dep_a3,
			"dep_b1": dep_b1,
		}

	def execute_report(self, filters=None):
		columns, data = execute(filters or {})
		self.assertGreater(len(columns), 0)
		return columns, data

	def execute_report_via_desk(self, filters=None):
		payload = run_query_report(report_name="Operational Review View", filters=filters or {})
		self.assertIn("result", payload)
		return payload.get("result") or []

	def test_report_executes(self):
		self.seed_dataset()
		_, data = self.execute_report()
		self.assertGreaterEqual(len(data), 4)

	def test_filter_executive_sponsor(self):
		seed = self.seed_dataset()
		_, data = self.execute_report({"executive_sponsor": seed["dep_a1"].executive_sponsor})
		self.assertTrue(data)
		self.assertTrue(all(row["executive_sponsor"] == seed["dep_a1"].executive_sponsor for row in data))

	def test_filter_workflow_owner(self):
		seed = self.seed_dataset()
		_, data = self.execute_report({"workflow_owner": seed["dep_b1"].accountable_owner})
		self.assertTrue(data)
		self.assertTrue(all(row["workflow_owner"] == seed["dep_b1"].accountable_owner for row in data))

	def test_filter_lighthouse_workflow_charter(self):
		seed = self.seed_dataset()
		_, data = self.execute_report({"lighthouse_workflow_charter": seed["charter_a"].name})
		self.assertTrue(data)
		self.assertTrue(
			all(row["lighthouse_workflow_charter"] == seed["charter_a"].name for row in data)
		)

	def test_filter_decision_record(self):
		seed = self.seed_dataset()
		_, data = self.execute_report({"decision_record": seed["decision_b"].name})
		self.assertEqual(len(data), 1)
		self.assertEqual(data[0]["decision_record"], seed["decision_b"].name)

	def test_filter_approval_state(self):
		self.seed_dataset()
		_, data = self.execute_report({"approval_state": "Submitted for Approval"})
		self.assertTrue(data)
		self.assertTrue(all(row["dependency_approval_state"] == "Submitted for Approval" for row in data))

	def test_filter_dependency_status(self):
		self.seed_dataset()
		_, data = self.execute_report({"dependency_status": "At Risk"})
		self.assertTrue(data)
		self.assertTrue(all(row["dependency_status"] == "At Risk" for row in data))

	def test_filter_dependency_criticality(self):
		self.seed_dataset()
		_, data = self.execute_report({"dependency_criticality": "Critical"})
		self.assertTrue(data)
		self.assertTrue(all(row["dependency_criticality"] == "Critical" for row in data))

	def test_filter_exception_required_any_via_desk(self):
		seed = self.seed_dataset()
		data = self.execute_report_via_desk({})
		row_names = {row["dependency_record"] for row in data}
		expected = {
			seed["dep_a1"].name,
			seed["dep_a2"].name,
			seed["dep_a3"].name,
			seed["dep_b1"].name,
		}
		self.assertTrue(expected.issubset(row_names))

	def test_filter_exception_required_yes_via_desk(self):
		seed = self.seed_dataset()
		data = self.execute_report_via_desk({"exception_required": "Yes"})
		self.assertTrue(data)
		row_names = {row["dependency_record"] for row in data}
		expected = {seed["dep_a1"].name, seed["dep_a2"].name, seed["dep_a3"].name}
		self.assertTrue(expected.issubset(row_names))
		self.assertTrue(all(row["exception_required"] == 1 for row in data))

	def test_filter_exception_required_no_via_desk(self):
		seed = self.seed_dataset()
		data = self.execute_report_via_desk({"exception_required": "No"})
		self.assertTrue(data)
		self.assertTrue(all(row["exception_required"] == 0 for row in data))
		row_names = {row["dependency_record"] for row in data}
		self.assertIn(seed["dep_b1"].name, row_names)

	def test_filter_date_range(self):
		self.seed_dataset()
		start = add_days(today(), -3)
		end = add_days(today(), 6)
		_, data = self.execute_report({"from_date": start, "to_date": end})
		self.assertTrue(data)
		for row in data:
			target_date = getdate(row["target_resolution_date"])
			self.assertGreaterEqual(target_date, getdate(start))
			self.assertLessEqual(target_date, getdate(end))

	def test_filter_show_overdue_only(self):
		self.seed_dataset()
		_, data = self.execute_report({"show_overdue_only": 1})
		self.assertTrue(data)
		self.assertTrue(all(row["overdue_flag"] == 1 for row in data))

	def test_derived_pending_sponsor_action(self):
		seed = self.seed_dataset()
		_, data = self.execute_report({"decision_record": seed["decision_a"].name})
		row_map = {row["dependency_record"]: row for row in data}
		self.assertEqual(row_map[seed["dep_a1"].name]["pending_sponsor_action"], 1)
		self.assertEqual(row_map[seed["dep_a2"].name]["pending_sponsor_action"], 0)

	def test_derived_overdue_flag(self):
		seed = self.seed_dataset()
		_, data = self.execute_report({"decision_record": seed["decision_a"].name})
		row_map = {row["dependency_record"]: row for row in data}
		self.assertEqual(row_map[seed["dep_a1"].name]["overdue_flag"], 1)
		self.assertEqual(row_map[seed["dep_a2"].name]["overdue_flag"], 0)
		self.assertEqual(row_map[seed["dep_a3"].name]["overdue_flag"], 0)

	def test_derived_at_risk_flag(self):
		seed = self.seed_dataset()
		_, data = self.execute_report({"decision_record": seed["decision_a"].name})
		row_map = {row["dependency_record"]: row for row in data}
		self.assertEqual(row_map[seed["dep_a1"].name]["at_risk_flag"], 1)
		self.assertEqual(row_map[seed["dep_a2"].name]["at_risk_flag"], 1)
		self.assertEqual(row_map[seed["dep_a3"].name]["at_risk_flag"], 0)

	def test_derived_open_exceptions_count(self):
		seed = self.seed_dataset()
		_, data = self.execute_report({"decision_record": seed["decision_a"].name})
		for row in data:
			self.assertEqual(row["open_exceptions_count"], 2)

	def test_one_row_per_dependency(self):
		seed = self.seed_dataset()
		_, data = self.execute_report()
		row_names = {row["dependency_record"] for row in data}
		expected = {
			seed["dep_a1"].name,
			seed["dep_a2"].name,
			seed["dep_a3"].name,
			seed["dep_b1"].name,
		}
		self.assertTrue(expected.issubset(row_names))
		self.assertEqual(len(row_names), len(data))

	def test_deterministic_ordering(self):
		seed = self.seed_dataset()
		_, data_first = self.execute_report({"decision_record": seed["decision_a"].name})
		_, data_second = self.execute_report({"decision_record": seed["decision_a"].name})
		self.assertEqual(
			[row["dependency_record"] for row in data_first],
			[row["dependency_record"] for row in data_second],
		)

	def test_allowed_roles_can_run_report(self):
		self.seed_dataset()
		for user in [
			self.owner_user,
			self.sponsor_user,
			self.operations_user,
			self.system_manager_user,
		]:
			frappe.set_user(user)
			_, data = self.execute_report()
			self.assertIsInstance(data, list)

	def test_disallowed_user_cannot_run_report(self):
		self.seed_dataset()
		frappe.set_user(self.unprivileged_user)
		self.assertRaises(frappe.PermissionError, execute, {})
