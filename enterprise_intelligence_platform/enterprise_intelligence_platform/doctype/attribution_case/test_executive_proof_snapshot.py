import copy

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import random_string

from enterprise_intelligence_platform.enterprise_intelligence_platform.doctype.attribution_case.test_attribution_case import (
	TestAttributionCase,
)

PRINT_FORMAT_NAME = "Executive Proof Snapshot"
TARGET_DOCTYPE = "Attribution Case"


class TestExecutiveProofSnapshot(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		TestAttributionCase.setUpClass()
		cls.fixture = TestAttributionCase("runTest")
		cls.no_access_user = cls.make_user_without_roles(f"eip_snapshot_viewer_{random_string(6)}@example.com")

	def tearDown(self):
		frappe.set_user("Administrator")

	@staticmethod
	def make_user_without_roles(email: str) -> str:
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

	def make_approved_case(self):
		decision = self.fixture.make_decision_doc()
		dependency_one = self.fixture.make_dependency_doc(decision=decision)
		dependency_two = self.fixture.make_dependency_doc(decision=decision)
		doc = self.fixture.make_attribution_case_doc(decision=decision, dependency=dependency_one)
		doc.set("attribution_chain_steps", [])
		doc.append(
			"attribution_chain_steps",
			{
				"sequence_no": 20,
				"step_summary": "Second chain step is intentionally listed first in storage.",
				"dependency_exception_record": dependency_one.name,
			},
		)
		doc.append(
			"attribution_chain_steps",
			{
				"sequence_no": 10,
				"step_summary": "First chain step is intentionally listed second in storage.",
				"dependency_exception_record": dependency_two.name,
			},
		)
		doc.set("attribution_evidence", [])
		doc.append(
			"attribution_evidence",
			{
				"evidence_type": "External",
				"supports_claim": 1,
				"evidence_reference": "External evidence B",
				"evidence_date": "2026-07-24",
				"evidence_note": "Second evidence row stored first.",
			},
		)
		doc.append(
			"attribution_evidence",
			{
				"evidence_type": "Document",
				"supports_claim": 0,
				"evidence_reference": "Document evidence A",
				"evidence_date": "2026-07-23",
				"evidence_note": "First evidence row stored second.",
			},
		)
		doc = doc.insert(ignore_permissions=True)
		doc.reload()
		doc.approval_state = "Submitted for Approval"
		doc.save(ignore_permissions=True)

		frappe.set_user(self.fixture.sponsor_user)
		doc.reload()
		doc.approval_state = "Approved"
		approved = doc.save(ignore_permissions=True)
		approved.reload()
		return approved

	def render_snapshot(self, doc):
		return frappe.get_print(doc=doc, print_format=PRINT_FORMAT_NAME, no_letterhead=1)

	def test_print_format_exists(self):
		print_format = frappe.get_doc("Print Format", PRINT_FORMAT_NAME)
		self.assertEqual(print_format.doc_type, TARGET_DOCTYPE)
		self.assertEqual(print_format.print_format_for, "DocType")
		self.assertEqual(print_format.standard, "Yes")

	def test_approved_case_renders_successfully(self):
		approved = self.make_approved_case()
		frappe.set_user(self.fixture.owner_user)
		html = frappe.get_print(
			TARGET_DOCTYPE,
			approved.name,
			print_format=PRINT_FORMAT_NAME,
			no_letterhead=1,
		)

		self.assertIn("Executive Proof Snapshot", html)
		self.assertIn(approved.attribution_title, html)
		self.assertIn("Executive Summary", html)
		self.assertIn("Governance Header", html)
		self.assertIn(approved.decision_record, html)
		self.assertIn(approved.lighthouse_workflow_charter, html)
		self.assertIn(approved.accountable_owner, html)
		self.assertIn(approved.executive_sponsor, html)
		self.assertIn("Confidence Score", html)
		self.assertIn("Ordered Attribution Chain", html)
		self.assertIn("Ordered Evidence", html)
		self.assertIn("Approval Metadata", html)
		self.assertIn(approved.approved_by, html)
		self.assertIn(approved.approved_on.strftime("%Y-%m-%d %H:%M:%S"), html)
		self.assertIn("Generated Timestamp", html)

	def test_draft_case_is_blocked(self):
		doc = self.fixture.make_attribution_case_doc().insert(ignore_permissions=True)
		frappe.set_user(self.fixture.owner_user)
		self.assertRaises(frappe.ValidationError, self.render_snapshot, doc)

	def test_rejected_case_is_blocked(self):
		doc = self.fixture.make_attribution_case_doc().insert(ignore_permissions=True)
		doc.reload()
		doc.approval_state = "Submitted for Approval"
		doc.save(ignore_permissions=True)

		doc.db_set("sponsor_decision_note", "Rejecting for proof snapshot coverage test.")
		doc.db_set("approval_state", "Rejected")
		doc.reload()

		frappe.set_user(self.fixture.owner_user)
		self.assertRaises(frappe.ValidationError, self.render_snapshot, doc)

	def test_permission_enforcement(self):
		approved = self.make_approved_case()
		frappe.set_user(self.no_access_user)
		self.assertRaises(
			frappe.PermissionError,
			frappe.get_print,
			TARGET_DOCTYPE,
			approved.name,
			print_format=PRINT_FORMAT_NAME,
			no_letterhead=1,
		)

	def test_chain_ordering_is_deterministic(self):
		approved = self.make_approved_case()
		approved.attribution_chain_steps[0].sequence_no = 30
		approved.attribution_chain_steps[1].sequence_no = 10
		approved.attribution_chain_steps[0].step_summary = "Sequence 30 should render after sequence 10."
		approved.attribution_chain_steps[1].step_summary = "Sequence 10 should render before sequence 30."
		html = self.render_snapshot(approved)

		self.assertLess(
			html.index("Sequence 10 should render before sequence 30."),
			html.index("Sequence 30 should render after sequence 10."),
		)

	def test_evidence_ordering_is_deterministic(self):
		approved = self.make_approved_case()
		approved.attribution_evidence[0].idx = 30
		approved.attribution_evidence[1].idx = 10
		approved.attribution_evidence[0].evidence_reference = "Rendered second"
		approved.attribution_evidence[1].evidence_reference = "Rendered first"
		html = self.render_snapshot(approved)

		self.assertLess(html.index("Rendered first"), html.index("Rendered second"))
		self.assertIn(">No<", html)
		self.assertIn(">Yes<", html)

	def test_rendering_does_not_mutate_document(self):
		approved = self.make_approved_case()
		snapshot_before = copy.deepcopy(approved.as_dict())
		self.render_snapshot(approved)
		snapshot_after = approved.as_dict()
		self.assertEqual(snapshot_after, snapshot_before)

	def test_linked_references_are_rendered(self):
		approved = self.make_approved_case()
		frappe.set_user(self.fixture.owner_user)
		html = frappe.get_print(
			TARGET_DOCTYPE,
			approved.name,
			print_format=PRINT_FORMAT_NAME,
			no_letterhead=1,
		)

		for token in (
			approved.decision_record,
			approved.lighthouse_workflow_charter,
			approved.attribution_chain_steps[0].dependency_exception_record,
			approved.attribution_chain_steps[1].dependency_exception_record,
		):
			self.assertIn(token, html)
