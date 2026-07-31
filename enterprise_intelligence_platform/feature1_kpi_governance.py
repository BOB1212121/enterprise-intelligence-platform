from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable

import frappe
from frappe import _
from frappe.utils import flt

REQUIRED_KPI_CODES = ("DRR", "DCT", "AER", "OCR", "RER")
REQUIRED_APPROVER_ROLES = (
	"EIP Workflow Owner",
	"EIP Executive Sponsor",
	"EIP Operations Manager",
)
MANDATORY_EVIDENCE_ITEMS = (
	"KPI matrix",
	"Comparative assessment matrix",
	"Risk assessment status",
	"Architecture impact review evidence",
	"Baseline compatibility review evidence",
	"Active gate evidence package",
)

GO_KPI_COMPLETENESS_THRESHOLD = 100.0
GO_EVIDENCE_COMPLETENESS_THRESHOLD = 95.0
MANDATORY_REVIEW_EVIDENCE_COMPLETENESS_MIN = 90.0
GO_COMPARATIVE_MARGIN = 10.0

HIGH_OR_CRITICAL = {"High", "Critical"}
APPROVED_STATE = "Approved"
BASELINE_ACCEPTED_STATE = "Baseline Accepted"


@dataclass(frozen=True)
class Feature1EvidenceResult:
	present_items: tuple[str, ...]
	missing_items: tuple[str, ...]
	completeness_pct: float
	active_gate_confirmed: int


@dataclass(frozen=True)
class Feature1KpiResult:
	observed_codes: tuple[str, ...]
	missing_codes: tuple[str, ...]
	duplicate_codes: tuple[str, ...]
	completeness_pct: float


@dataclass(frozen=True)
class Feature1ComparativeResult:
	weighting_model: str | None
	weighted_candidate_a_score: float | None
	weighted_candidate_b_score: float | None
	comparative_delta: float | None
	completeness_pct: float
	missing_dimensions: tuple[str, ...]


@dataclass(frozen=True)
class Feature1ApproverResult:
	required_roles: tuple[str, ...]
	approved_roles: tuple[str, ...]
	missing_roles: tuple[str, ...]
	unapproved_roles: tuple[str, ...]
	unanimity_confirmed: int


@dataclass(frozen=True)
class Feature1RelatedRecords:
	decision_records: tuple[Any, ...]
	dependency_records: tuple[Any, ...]
	attribution_records: tuple[Any, ...]


@dataclass(frozen=True)
class Feature1ReviewResult:
	lighthouse_workflow_charter: str
	decision_record: str | None
	comparative_weighting_model: str | None
	weighted_candidate_a_score: float | None
	weighted_candidate_b_score: float | None
	kpi_completeness_pct: float
	evidence_completeness_pct: float
	comparative_delta: float | None
	review_band_flag: int
	review_outcome: str
	adjudication_reason: str
	mandatory_evidence_present: int
	mandatory_evidence_total: int
	missing_evidence_items: str
	resolved_dependency_count: int
	approved_attribution_count: int
	unresolved_high_critical_count: int
	baseline_compatibility_confirmed: int
	baseline_change_trigger: int
	approver_unanimity_confirmed: int
	required_approver_roles: str
	approved_approver_roles: str
	missing_approver_roles: str
	unapproved_approver_roles: str

	def as_dict(self) -> dict[str, Any]:
		return {
			"lighthouse_workflow_charter": self.lighthouse_workflow_charter,
			"decision_record": self.decision_record or "",
			"comparative_weighting_model": self.comparative_weighting_model or "",
			"weighted_candidate_a_score": self.weighted_candidate_a_score,
			"weighted_candidate_b_score": self.weighted_candidate_b_score,
			"kpi_completeness_pct": self.kpi_completeness_pct,
			"evidence_completeness_pct": self.evidence_completeness_pct,
			"comparative_delta": self.comparative_delta,
			"review_band_flag": self.review_band_flag,
			"review_outcome": self.review_outcome,
			"adjudication_reason": self.adjudication_reason,
			"mandatory_evidence_present": self.mandatory_evidence_present,
			"mandatory_evidence_total": self.mandatory_evidence_total,
			"missing_evidence_items": self.missing_evidence_items,
			"resolved_dependency_count": self.resolved_dependency_count,
			"approved_attribution_count": self.approved_attribution_count,
			"unresolved_high_critical_count": self.unresolved_high_critical_count,
			"baseline_compatibility_confirmed": self.baseline_compatibility_confirmed,
			"baseline_change_trigger": self.baseline_change_trigger,
			"approver_unanimity_confirmed": self.approver_unanimity_confirmed,
			"required_approver_roles": self.required_approver_roles,
			"approved_approver_roles": self.approved_approver_roles,
			"missing_approver_roles": self.missing_approver_roles,
			"unapproved_approver_roles": self.unapproved_approver_roles,
		}


def evaluate_feature1_review(
	*,
	lighthouse_workflow_charter: str,
	candidate_a_score: float | int | str | None = None,
	candidate_b_score: float | int | str | None = None,
	comparative_weighting_model: str | None = None,
	decision_record: str | None = None,
	governance_package: dict[str, Any] | str | None = None,
	baseline_change_trigger: bool = False,
) -> Feature1ReviewResult:
	charter = frappe.get_doc("Lighthouse Workflow Charter", lighthouse_workflow_charter)
	_frappesafe_has_read_permissions()

	related = fetch_related_records(charter.name, decision_record=decision_record)
	package = _resolve_governance_package(
		governance_package=governance_package,
	)

	kpi_result = calculate_kpi_result(charter, package["kpi_matrix"])
	comparative_result = calculate_comparative_result(package["comparative_assessment"])
	approver_result = calculate_approver_result(package["approver_votes"])

	approved_attribution_count = count_approved_attributions(related.attribution_records)
	approved_decision_present = bool(related.decision_records) and all(
		decision.approval_state == APPROVED_STATE for decision in related.decision_records[:1]
	)
	baseline_compatibility_confirmed = int(
		charter.approval_state == BASELINE_ACCEPTED_STATE
		and approved_decision_present
		and approved_attribution_count > 0
	)
	unresolved_high_critical_count = count_unresolved_high_critical_dependencies(related.dependency_records)

	evidence_result = calculate_evidence_result(
		evidence_package=package["evidence_package"],
		kpi_result=kpi_result,
		comparative_assessment_present=bool(
			comparative_result.weighting_model and comparative_result.completeness_pct == 100.0
		),
		has_decision=bool(related.decision_records),
		has_dependency=bool(related.dependency_records),
		has_approved_attribution=approved_attribution_count > 0,
		baseline_compatibility_confirmed=bool(baseline_compatibility_confirmed),
		approver_unanimity_confirmed=bool(approver_result.unanimity_confirmed),
	)

	comparative_delta = comparative_result.comparative_delta
	review_band_flag = int(
		(
			comparative_result.weighted_candidate_a_score is not None
			and comparative_result.weighted_candidate_b_score is not None
			and comparative_result.weighted_candidate_a_score >= comparative_result.weighted_candidate_b_score
			and comparative_delta is not None
			and comparative_delta < GO_COMPARATIVE_MARGIN
		)
		or (GO_EVIDENCE_COMPLETENESS_THRESHOLD > evidence_result.completeness_pct >= MANDATORY_REVIEW_EVIDENCE_COMPLETENESS_MIN)
	)

	outcome, reason = determine_review_outcome(
		kpi_completeness_pct=kpi_result.completeness_pct,
		evidence_completeness_pct=evidence_result.completeness_pct,
		weighted_candidate_a_score=comparative_result.weighted_candidate_a_score,
		weighted_candidate_b_score=comparative_result.weighted_candidate_b_score,
		comparative_assessment_present=bool(
			comparative_result.weighting_model and comparative_result.completeness_pct == 100.0
		),
		unresolved_high_critical_count=unresolved_high_critical_count,
		baseline_compatibility_confirmed=bool(baseline_compatibility_confirmed),
		baseline_change_trigger=bool(baseline_change_trigger),
		approver_unanimity_confirmed=bool(approver_result.unanimity_confirmed),
	)

	return Feature1ReviewResult(
		lighthouse_workflow_charter=charter.name,
		decision_record=related.decision_records[0].name if related.decision_records else None,
		comparative_weighting_model=comparative_result.weighting_model,
		weighted_candidate_a_score=comparative_result.weighted_candidate_a_score,
		weighted_candidate_b_score=comparative_result.weighted_candidate_b_score,
		kpi_completeness_pct=kpi_result.completeness_pct,
		evidence_completeness_pct=evidence_result.completeness_pct,
		comparative_delta=comparative_delta,
		review_band_flag=review_band_flag,
		review_outcome=outcome,
		adjudication_reason=reason,
		mandatory_evidence_present=len(evidence_result.present_items),
		mandatory_evidence_total=len(MANDATORY_EVIDENCE_ITEMS),
		missing_evidence_items=", ".join(evidence_result.missing_items) if evidence_result.missing_items else "—",
		resolved_dependency_count=len(related.dependency_records),
		approved_attribution_count=approved_attribution_count,
		unresolved_high_critical_count=unresolved_high_critical_count,
		baseline_compatibility_confirmed=baseline_compatibility_confirmed,
		baseline_change_trigger=int(bool(baseline_change_trigger)),
		approver_unanimity_confirmed=approver_result.unanimity_confirmed,
		required_approver_roles=", ".join(approver_result.required_roles),
		approved_approver_roles=", ".join(approver_result.approved_roles) if approver_result.approved_roles else "—",
		missing_approver_roles=", ".join(approver_result.missing_roles) if approver_result.missing_roles else "—",
		unapproved_approver_roles=", ".join(approver_result.unapproved_roles) if approver_result.unapproved_roles else "—",
	)


def calculate_kpi_result(charter, kpi_matrix: Any | None = None) -> Feature1KpiResult:
	rows = _normalize_rows(kpi_matrix)
	baseline_rows = {str(row.kpi_code): row for row in list(getattr(charter, "baseline_kpis", []) or [])}
	observed_codes: list[str] = []
	duplicate_codes: list[str] = []
	valid_codes: list[str] = []

	rows_by_code: dict[str, Any] = {}
	for row in rows:
		kpi_code = _normalize_optional_text(_read_value(row, "kpi_code"))
		if not kpi_code:
			continue
		if kpi_code in rows_by_code:
			duplicate_codes.append(kpi_code)
		rows_by_code[kpi_code] = row
		observed_codes.append(kpi_code)

	for kpi_code in REQUIRED_KPI_CODES:
		row = rows_by_code.get(kpi_code)
		if row is None:
			continue
		if _kpi_row_is_valid(row, baseline_rows.get(kpi_code)):
			valid_codes.append(kpi_code)

	missing_codes = sorted(set(REQUIRED_KPI_CODES) - set(rows_by_code))
	completeness_pct = round(len(valid_codes) / len(REQUIRED_KPI_CODES) * 100, 2)

	return Feature1KpiResult(
		observed_codes=tuple(observed_codes),
		missing_codes=tuple(missing_codes),
		duplicate_codes=tuple(sorted(set(duplicate_codes))),
		completeness_pct=completeness_pct,
	)


def calculate_comparative_result(comparative_assessment: Any | None) -> Feature1ComparativeResult:
	assessment = _normalize_mapping(comparative_assessment)
	model_name = _normalize_optional_text(assessment.get("weighting_model"))
	dimensions = _normalize_rows(assessment.get("dimensions"))
	missing_dimensions: list[str] = []
	weighted_a = 0.0
	weighted_b = 0.0
	weight_sum = 0.0
	valid_dimensions = 0

	for dimension in dimensions:
		name = _normalize_optional_text(_read_value(dimension, "name"))
		weight = _normalize_optional_float(_read_value(dimension, "weight"))
		a_score = _normalize_optional_float(_read_value(dimension, "candidate_a_score"))
		b_score = _normalize_optional_float(_read_value(dimension, "candidate_b_score"))
		if not name or weight is None or a_score is None or b_score is None or weight <= 0:
			missing_dimensions.append(name or "(unnamed dimension)")
			continue
		valid_dimensions += 1
		weight_sum += weight
		weighted_a += weight * a_score
		weighted_b += weight * b_score

	if valid_dimensions == 0 or weight_sum <= 0:
		return Feature1ComparativeResult(
			weighting_model=model_name,
			weighted_candidate_a_score=None,
			weighted_candidate_b_score=None,
			comparative_delta=None,
			completeness_pct=0.0,
			missing_dimensions=tuple(missing_dimensions),
		)

	weighted_candidate_a_score = round(weighted_a / weight_sum, 2)
	weighted_candidate_b_score = round(weighted_b / weight_sum, 2)
	comparative_delta = round(weighted_candidate_a_score - weighted_candidate_b_score, 2)
	completeness_pct = round(valid_dimensions / len(dimensions) * 100, 2) if dimensions else 0.0

	return Feature1ComparativeResult(
		weighting_model=model_name,
		weighted_candidate_a_score=weighted_candidate_a_score,
		weighted_candidate_b_score=weighted_candidate_b_score,
		comparative_delta=comparative_delta,
		completeness_pct=completeness_pct,
		missing_dimensions=tuple(missing_dimensions),
	)


def calculate_approver_result(approver_votes: Any | None) -> Feature1ApproverResult:
	votes = _normalize_rows(approver_votes)
	by_role = {}
	for vote in votes:
		role = _normalize_optional_text(_read_value(vote, "role"))
		if role:
			by_role[role] = vote

	approved_roles: list[str] = []
	missing_roles: list[str] = []
	unapproved_roles: list[str] = []
	for role in REQUIRED_APPROVER_ROLES:
		vote = by_role.get(role)
		if vote is None:
			missing_roles.append(role)
			continue
		if _normalize_optional_truthy(_read_value(vote, "approved")):
			approved_roles.append(role)
		else:
			unapproved_roles.append(role)

	unanimity_confirmed = int(not missing_roles and not unapproved_roles)
	return Feature1ApproverResult(
		required_roles=REQUIRED_APPROVER_ROLES,
		approved_roles=tuple(approved_roles),
		missing_roles=tuple(missing_roles),
		unapproved_roles=tuple(unapproved_roles),
		unanimity_confirmed=unanimity_confirmed,
	)


def calculate_evidence_result(
	*,
	evidence_package: Any | None,
	kpi_result: Feature1KpiResult,
	comparative_assessment_present: bool,
	has_decision: bool,
	has_dependency: bool,
	has_approved_attribution: bool,
	baseline_compatibility_confirmed: bool,
	approver_unanimity_confirmed: bool,
) -> Feature1EvidenceResult:
	rows = _normalize_rows(evidence_package)
	by_label = {}
	for row in rows:
		label = _normalize_optional_text(_read_value(row, "label"))
		if label:
			by_label[label] = row

	present_items: list[str] = []
	missing_items: list[str] = []

	kpi_matrix_present = kpi_result.completeness_pct == 100.0 and not kpi_result.missing_codes and not kpi_result.duplicate_codes
	_add_evidence_item(present_items, missing_items, "KPI matrix", kpi_matrix_present and _item_reviewable(by_label.get("KPI matrix")))
	_add_evidence_item(
		present_items,
		missing_items,
		"Comparative assessment matrix",
		comparative_assessment_present and _item_reviewable(by_label.get("Comparative assessment matrix")),
	)
	_add_evidence_item(present_items, missing_items, "Risk assessment status", has_dependency and _item_reviewable(by_label.get("Risk assessment status")))
	_add_evidence_item(
		present_items,
		missing_items,
		"Architecture impact review evidence",
		has_decision and _item_reviewable(by_label.get("Architecture impact review evidence")),
	)
	_add_evidence_item(
		present_items,
		missing_items,
		"Baseline compatibility review evidence",
		baseline_compatibility_confirmed and _item_reviewable(by_label.get("Baseline compatibility review evidence")),
	)
	active_gate_present = all(
		(
			kpi_matrix_present,
			comparative_assessment_present,
			has_decision,
			has_dependency,
			has_approved_attribution,
			baseline_compatibility_confirmed,
			approver_unanimity_confirmed,
		)
	)
	_add_evidence_item(
		present_items,
		missing_items,
		"Active gate evidence package",
		active_gate_present and _item_reviewable(by_label.get("Active gate evidence package")),
	)

	completeness_pct = round(len(present_items) / len(MANDATORY_EVIDENCE_ITEMS) * 100, 2)
	return Feature1EvidenceResult(
		present_items=tuple(present_items),
		missing_items=tuple(missing_items),
		completeness_pct=completeness_pct,
		active_gate_confirmed=int(active_gate_present),
	)


def determine_review_outcome(
	*,
	kpi_completeness_pct: float,
	evidence_completeness_pct: float,
	weighted_candidate_a_score: float | None,
	weighted_candidate_b_score: float | None,
	comparative_assessment_present: bool,
	unresolved_high_critical_count: int,
	baseline_compatibility_confirmed: bool,
	baseline_change_trigger: bool,
	approver_unanimity_confirmed: bool,
) -> tuple[str, str]:
	if baseline_change_trigger:
		return "NO-GO", _("Unresolved Baseline Change trigger requires ADR disposition.")

	if not comparative_assessment_present:
		return "NO-GO", _("Comparative assessment matrix is incomplete.")

	if kpi_completeness_pct < GO_KPI_COMPLETENESS_THRESHOLD:
		return "NO-GO", _("KPI completeness is below the required 100% threshold.")

	if evidence_completeness_pct < MANDATORY_REVIEW_EVIDENCE_COMPLETENESS_MIN:
		return "NO-GO", _("Evidence completeness is below the mandatory review minimum.")

	if weighted_candidate_a_score is None or weighted_candidate_b_score is None:
		return "NO-GO", _("Comparative scores are missing.")

	if weighted_candidate_a_score < weighted_candidate_b_score:
		return "NO-GO", _("Candidate A is below Candidate B.")

	if unresolved_high_critical_count > 0:
		return "NO-GO", _("Unresolved High or Critical findings remain.")

	if not baseline_compatibility_confirmed:
		return "NO-GO", _("Baseline compatibility review is not confirmed.")

	if not approver_unanimity_confirmed:
		return "NO-GO", _("Required approvers have not unanimously approved.")

	if weighted_candidate_a_score >= weighted_candidate_b_score + GO_COMPARATIVE_MARGIN and evidence_completeness_pct >= GO_EVIDENCE_COMPLETENESS_THRESHOLD:
		return "GO", _("All go-threshold conditions are satisfied.")

	return "GO", _("Mandatory review band resolved through deterministic approval rule.")


@dataclass(frozen=True)
class _RelatedRecords:
	decision_records: tuple[Any, ...]
	dependency_records: tuple[Any, ...]
	attribution_records: tuple[Any, ...]


def fetch_related_records(charter_name: str, decision_record: str | None = None) -> _RelatedRecords:
	decision_filters = {"lighthouse_workflow_charter": charter_name}
	if decision_record:
		decision_filters["name"] = decision_record
	decision_rows = frappe.get_all(
		"Decision Record",
		filters=decision_filters,
		fields=["name", "approval_state", "approved_by", "approved_on", "modified"],
		order_by="modified desc, name desc",
	)
	decision_docs = tuple(frappe.get_doc("Decision Record", row.name) for row in decision_rows)
	selected_decision = decision_docs[:1]

	dependency_docs: tuple[Any, ...] = ()
	attribution_docs: tuple[Any, ...] = ()
	if selected_decision:
		dependency_rows = frappe.get_all(
			"Dependency Exception Record",
			filters={"decision_record": selected_decision[0].name},
			fields=["name", "approval_state", "dependency_status", "dependency_criticality", "modified"],
			order_by="modified desc, name desc",
		)
		dependency_docs = tuple(
			frappe.get_doc("Dependency Exception Record", row.name) for row in dependency_rows
		)

		attribution_rows = frappe.get_all(
			"Attribution Case",
			filters={"decision_record": selected_decision[0].name},
			fields=["name", "approval_state", "confidence_score", "modified"],
			order_by="modified desc, name desc",
		)
		attribution_docs = tuple(
			frappe.get_doc("Attribution Case", row.name) for row in attribution_rows
		)

	return _RelatedRecords(
		decision_records=decision_docs,
		dependency_records=dependency_docs,
		attribution_records=attribution_docs,
	)


def count_unresolved_high_critical_dependencies(dependency_records: Iterable[Any]) -> int:
	count = 0
	for record in dependency_records:
		criticality = _normalize_optional_text(getattr(record, "dependency_criticality", None))
		status = _normalize_optional_text(getattr(record, "dependency_status", None))
		if criticality in HIGH_OR_CRITICAL and status != "Resolved":
			count += 1
	return count


def count_approved_attributions(attribution_records: Iterable[Any]) -> int:
	return sum(1 for record in attribution_records if _normalize_optional_text(getattr(record, "approval_state", None)) == APPROVED_STATE)


def _resolve_governance_package(
	*,
	governance_package: dict[str, Any] | str | None,
) -> dict[str, Any]:
	if governance_package is None:
		frappe.throw(
			_("Feature 1 governance package is required and must include KPI matrix, comparative assessment, evidence package, and approver votes."),
			exc=frappe.ValidationError,
		)

	package = _normalize_mapping(governance_package)
	sections = {
		"kpi_matrix": package.get("kpi_matrix"),
		"comparative_assessment": package.get("comparative_assessment"),
		"evidence_package": package.get("evidence_package"),
		"approver_votes": package.get("approver_votes"),
	}

	missing_sections = [name for name, value in sections.items() if value is None]
	if missing_sections:
		frappe.throw(
			_("Feature 1 governance package is missing required section(s): {sections}.").format(
				sections=", ".join(sorted(missing_sections))
			),
			exc=frappe.ValidationError,
		)

	return sections


def _normalize_rows(value: Any | None) -> tuple[Any, ...]:
	if value is None:
		return ()
	if isinstance(value, str):
		text = value.strip()
		if not text:
			return ()
		parsed = json.loads(text)
		return _normalize_rows(parsed)
	if isinstance(value, dict):
		if "rows" in value:
			return _normalize_rows(value["rows"])
		if "items" in value:
			return _normalize_rows(value["items"])
		if "dimensions" in value:
			return _normalize_rows(value["dimensions"])
		return (value,)
	if isinstance(value, (list, tuple)):
		return tuple(value)
	return (value,)


def _normalize_mapping(value: Any | None) -> dict[str, Any]:
	if value is None:
		return {}
	if isinstance(value, str):
		text = value.strip()
		if not text:
			return {}
		parsed = json.loads(text)
		return _normalize_mapping(parsed)
	if isinstance(value, dict):
		return dict(value)
	return {}


def _kpi_row_is_valid(row: Any, baseline_row: Any | None) -> bool:
	if _normalize_optional_text(_read_value(row, "formula")) is None:
		return False
	if _normalize_optional_text(_read_value(row, "source_owner")) is None:
		return False
	measurement_window = _normalize_mapping(_read_value(row, "measurement_window"))
	if _normalize_optional_text(measurement_window.get("start")) is None:
		return False
	if _normalize_optional_text(measurement_window.get("end")) is None:
		return False
	if _normalize_optional_text(_read_value(row, "threshold")) is None and _read_value(row, "threshold") is None:
		return False
	if _normalize_optional_text(_read_value(row, "pass_fail_rule")) is None:
		return False
	if baseline_row is not None:
		baseline_value = _read_value(row, "baseline_value")
		if baseline_value is not None and flt(baseline_value) != flt(getattr(baseline_row, "baseline_value", baseline_value)):
			return False
	return True


def _item_reviewable(row: Any | None) -> bool:
	if row is None:
		return False
	return _normalize_optional_truthy(_read_value(row, "reviewable"))


def _read_value(row: Any, field_name: str) -> Any:
	if isinstance(row, dict):
		return row.get(field_name)
	return getattr(row, field_name, None)


def _normalize_optional_text(value: Any) -> str | None:
	if value is None:
		return None
	text = str(value).strip()
	return text or None


def _normalize_optional_float(value: Any) -> float | None:
	if value is None or value == "":
		return None
	return round(flt(value), 2)


def _normalize_optional_truthy(value: Any) -> bool:
	if isinstance(value, str):
		return value.strip().lower() in {"1", "true", "yes", "y", "on"}
	return bool(value)


def _frappesafe_has_read_permissions() -> None:
	for doctype in (
		"Lighthouse Workflow Charter",
		"Decision Record",
		"Dependency Exception Record",
		"Attribution Case",
	):
		frappe.has_permission(doctype, ptype="read", throw=True)


def _add_evidence_item(present_items: list[str], missing_items: list[str], label: str, is_present: bool) -> None:
	if is_present:
		present_items.append(label)
	else:
		missing_items.append(label)


__all__ = [
	"MANDATORY_EVIDENCE_ITEMS",
	"REQUIRED_APPROVER_ROLES",
	"REQUIRED_KPI_CODES",
	"Feature1ApproverResult",
	"Feature1ComparativeResult",
	"Feature1EvidenceResult",
	"Feature1KpiResult",
	"Feature1RelatedRecords",
	"Feature1ReviewResult",
	"calculate_approver_result",
	"calculate_comparative_result",
	"calculate_evidence_result",
	"calculate_kpi_result",
	"count_approved_attributions",
	"count_unresolved_high_critical_dependencies",
	"determine_review_outcome",
	"evaluate_feature1_review",
	"fetch_related_records",
]
