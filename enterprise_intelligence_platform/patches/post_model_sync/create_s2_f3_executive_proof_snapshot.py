from textwrap import dedent

import frappe

PRINT_FORMAT_NAME = "Executive Proof Snapshot"
TARGET_DOCTYPE = "Attribution Case"
MODULE_NAME = "Enterprise Intelligence Platform"

PRINT_FORMAT_HTML = dedent(
	"""
	{% if doc.approval_state != "Approved" %}
	{{ frappe.throw(_("Executive Proof Snapshot is only available for approved Attribution Cases.")) }}
	{% endif %}
	{% if not frappe.db.exists("Decision Record", doc.decision_record) %}
	{{ frappe.throw(_("Linked Decision Record could not be resolved.")) }}
	{% endif %}
	{% if not frappe.db.exists("Lighthouse Workflow Charter", doc.lighthouse_workflow_charter) %}
	{{ frappe.throw(_("Linked Lighthouse Workflow Charter could not be resolved.")) }}
	{% endif %}
	{% set decision = frappe.get_doc("Decision Record", doc.decision_record) %}
	{% set charter = frappe.get_doc("Lighthouse Workflow Charter", doc.lighthouse_workflow_charter) %}
	{% set chain_rows = doc.attribution_chain_steps | sort(attribute="sequence_no") %}
	{% set evidence_rows = doc.attribution_evidence | sort(attribute="idx") %}
	<div class="executive-proof-snapshot">
	  <h1>Executive Proof Snapshot</h1>

	  <section class="snapshot-section">
	    <h2>Executive Summary</h2>
	    <p>{{ doc.attribution_summary }}</p>
	  </section>

	  <section class="snapshot-section">
	    <h2>Governance Header</h2>
	    <table class="snapshot-table">
	      <tr><th>Attribution Case</th><td>{{ doc.name }}</td></tr>
	      <tr><th>Decision Record</th><td>{{ decision.name }} — {{ decision.decision_title }}</td></tr>
	      <tr><th>Lighthouse Workflow Charter</th><td>{{ charter.name }} — {{ charter.workflow_name }}</td></tr>
	      <tr><th>Workflow Owner</th><td>{{ doc.accountable_owner }}</td></tr>
	      <tr><th>Executive Sponsor</th><td>{{ doc.executive_sponsor }}</td></tr>
	    </table>
	  </section>

	  <section class="snapshot-section">
	    <h2>Attribution Summary</h2>
	    <p>{{ doc.attribution_summary }}</p>
	  </section>

	  <section class="snapshot-section">
	    <h2>Confounder Summary</h2>
	    <p>{{ doc.confounder_summary }}</p>
	  </section>

	  <section class="snapshot-section">
	    <h2>Confidence</h2>
	    <table class="snapshot-table">
	      <tr><th>Confidence Score</th><td>{{ doc.confidence_score }}</td></tr>
	      <tr><th>Confidence Rationale</th><td>{{ doc.confidence_rationale }}</td></tr>
	    </table>
	  </section>

	  <section class="snapshot-section">
	    <h2>Ordered Attribution Chain</h2>
	    <table class="snapshot-table">
	      <thead>
	        <tr>
	          <th>Sequence No</th>
	          <th>Step Summary</th>
	          <th>Dependency Exception Record</th>
	          <th>Dependency Title</th>
	        </tr>
	      </thead>
	      <tbody>
	        {% for row in chain_rows %}
	          {% if row.dependency_exception_record %}
	            {% if not frappe.db.exists("Dependency Exception Record", row.dependency_exception_record) %}
	            {{ frappe.throw(_("Linked Dependency Exception Record could not be resolved.")) }}
	            {% endif %}
	            {% set dependency = frappe.get_doc("Dependency Exception Record", row.dependency_exception_record) %}
	          {% else %}
	            {% set dependency = none %}
	          {% endif %}
	          <tr>
	            <td>{{ row.sequence_no }}</td>
	            <td>{{ row.step_summary }}</td>
	            <td>{% if dependency %}{{ dependency.name }}{% else %}—{% endif %}</td>
	            <td>{% if dependency %}{{ dependency.dependency_title }}{% else %}—{% endif %}</td>
	          </tr>
	        {% endfor %}
	      </tbody>
	    </table>
	  </section>

	  <section class="snapshot-section">
	    <h2>Ordered Evidence</h2>
	    <table class="snapshot-table">
	      <thead>
	        <tr>
	          <th>Evidence Type</th>
	          <th>Supports Claim</th>
	          <th>Evidence Reference</th>
	          <th>Evidence Date</th>
	          <th>Evidence Note</th>
	        </tr>
	      </thead>
	      <tbody>
	        {% for row in evidence_rows %}
	          <tr>
	            <td>{{ row.evidence_type }}</td>
	            <td>{% if row.supports_claim %}Yes{% else %}No{% endif %}</td>
	            <td>{{ row.evidence_reference }}</td>
	            <td>{{ row.evidence_date or "—" }}</td>
	            <td>{{ row.evidence_note or "—" }}</td>
	          </tr>
	        {% endfor %}
	      </tbody>
	    </table>
	  </section>

	  {% if doc.sponsor_decision_note %}
	  <section class="snapshot-section">
	    <h2>Sponsor Decision Note</h2>
	    <p>{{ doc.sponsor_decision_note }}</p>
	  </section>
	  {% endif %}

	  <section class="snapshot-section">
	    <h2>Approval Metadata</h2>
	    <table class="snapshot-table">
	      <tr><th>Approved By</th><td>{{ doc.approved_by }}</td></tr>
	      <tr><th>Approved On</th><td>{{ doc.approved_on.strftime("%Y-%m-%d %H:%M:%S") if doc.approved_on else "—" }}</td></tr>
	    </table>
	  </section>

	  <footer class="snapshot-footer">
	    <p>Document Identifiers: {{ doc.name }} | {{ doc.decision_record }} | {{ doc.lighthouse_workflow_charter }}</p>
	    <p>Generated Timestamp: {{ frappe.utils.now_datetime().strftime("%Y-%m-%d %H:%M:%S") }}</p>
	  </footer>
	</div>
	"""
).strip()

PRINT_FORMAT_CSS = dedent(
	"""
	.executive-proof-snapshot {
		font-family: Inter, Arial, sans-serif;
		font-size: 12px;
		line-height: 1.5;
		color: #111827;
	}

	.executive-proof-snapshot h1,
	.executive-proof-snapshot h2 {
		color: #0f172a;
		margin-bottom: 8px;
	}

	.snapshot-section {
		margin-bottom: 16px;
	}

	.snapshot-table {
		width: 100%;
		border-collapse: collapse;
		margin-top: 8px;
	}

	.snapshot-table th,
	.snapshot-table td {
		border: 1px solid #d1d5db;
		padding: 6px 8px;
		vertical-align: top;
	}

	.snapshot-table th {
		background: #f8fafc;
		text-align: left;
		width: 220px;
	}

	.snapshot-footer {
		margin-top: 24px;
		padding-top: 8px;
		border-top: 1px solid #e5e7eb;
		font-size: 10px;
		color: #4b5563;
	}
	"""
).strip()


def execute():
	ensure_print_format()


def ensure_print_format():
	if frappe.db.exists("Print Format", PRINT_FORMAT_NAME):
		print_format = frappe.get_doc("Print Format", PRINT_FORMAT_NAME)
	else:
		print_format = frappe.new_doc("Print Format")

	print_format.print_format_for = "DocType"
	print_format.name = PRINT_FORMAT_NAME
	print_format.doc_type = TARGET_DOCTYPE
	print_format.report = None
	print_format.module = MODULE_NAME
	print_format.standard = "Yes"
	print_format.custom_format = 0
	print_format.disabled = 0
	print_format.print_format_type = "Jinja"
	print_format.raw_printing = 0
	print_format.html = PRINT_FORMAT_HTML
	print_format.css = PRINT_FORMAT_CSS
	print_format.print_format_builder = 0
	print_format.print_format_builder_beta = 0

	if print_format.is_new():
		print_format.insert(ignore_permissions=True)
	else:
		print_format.save(ignore_permissions=True)
