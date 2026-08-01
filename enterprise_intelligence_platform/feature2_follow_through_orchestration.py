from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, now_datetime, nowdate

GOVERNANCE_ROLES = (
	"EIP Workflow Owner",
	"EIP Executive Sponsor",
	"EIP Operations Manager",
	"System Manager",
)

FEATURE2_REPORT_NAME = "Feature 2 Follow-Through Prioritization Review"
FEATURE2_REPORT_MODULE = "Enterprise Intelligence Platform"
FEATURE2_REPORT_REF_DOCTYPE = "Decision Record"
FEATURE2_AUDIT_LOGGER_NAME = "enterprise_intelligence_platform.feature2"

PERF_PARAMETER_DEFAULTS = {
	"perf_max_ranking_execution_duration": "PERF_MAX_RANKING_EXECUTION_DURATION",
	"perf_min_items_per_review_window": "PERF_MIN_ITEMS_PER_REVIEW_WINDOW",
	"perf_ordering_stability_tolerance": "PERF_ORDERING_STABILITY_TOLERANCE",
	"perf_supported_ranking_dataset_profile": "PERF_SUPPORTED_RANKING_DATASET_PROFILE",
	"perf_degradation_policy_on_capacity_exceeded": "PERF_DEGRADATION_POLICY_ON_CAPACITY_EXCEEDED",
	"perf_supported_review_window_definition": "PERF_SUPPORTED_REVIEW_WINDOW_DEFINITION",
}
REQUIRED_APPROVAL_METADATA_KEYS = (
	"approval_status",
	"approval_reference",
	"approved_by_role",
)

ALLOWED_ITEM_TYPES = {
	"Decision Approval Readiness",
	"Dependency Risk",
	"Attribution Confidence",
}
ALLOWED_SOURCE_DOCTYPES = {
	"Decision Record",
	"Dependency Exception Record",
	"Attribution Case",
}
PROHIBITED_NON_DUPLICATION_SOURCES = {
	"Operational Review View",
	"Executive Proof Snapshot",
}
PROHIBITED_DUPLICATE_PERSISTENCE_DOCTYPES = (
	"Follow Through Item",
	"Follow Through Cycle",
	"Escalation Case",
	"FollowThroughItem",
	"FollowThroughCycle",
	"EscalationCase",
)

PRIORITY_TYPE_BASE_WEIGHT = {
	"Decision Approval Readiness": 60.0,
	"Dependency Risk": 70.0,
	"Attribution Confidence": 50.0,
}
DEPENDENCY_CRITICALITY_WEIGHT = {
	"Critical": 30.0,
	"High": 20.0,
	"Medium": 10.0,
	"Low": 0.0,
}
PRIORITY_BAND_BY_MIN_SCORE = (
	("Critical", 90.0),
	("High", 70.0),
	("Medium", 40.0),
	("Low", 0.0),
)
SOURCE_DOCTYPE_RANK = {
	"Dependency Exception Record": 0,
	"Decision Record": 1,
	"Attribution Case": 2,
}
APPROVED_STATE = "Approved"
RESOLVED_STATUS = "Resolved"
HIGH_OR_CRITICAL = {"High", "Critical"}
ATTRIBUTION_CONFIDENCE_THRESHOLD = 0.70


@dataclass(frozen=True)
class Feature2AcceptanceParameters:
	perf_max_ranking_execution_duration: str
	perf_min_items_per_review_window: str
	perf_ordering_stability_tolerance: str
	perf_supported_ranking_dataset_profile: str
	perf_degradation_policy_on_capacity_exceeded: str
	perf_supported_review_window_definition: str

	def as_dict(self) -> dict[str, str]:
		return {
			"perf_max_ranking_execution_duration": self.perf_max_ranking_execution_duration,
			"perf_min_items_per_review_window": self.perf_min_items_per_review_window,
			"perf_ordering_stability_tolerance": self.perf_ordering_stability_tolerance,
			"perf_supported_ranking_dataset_profile": self.perf_supported_ranking_dataset_profile,
			"perf_degradation_policy_on_capacity_exceeded": self.perf_degradation_policy_on_capacity_exceeded,
			"perf_supported_review_window_definition": self.perf_supported_review_window_definition,
		}


@dataclass(frozen=True)
class Feature2FollowThroughItem:
	lighthouse_workflow_charter: str
	decision_record: str
	review_window_start: str
	review_window_end: str
	policy_version: str
	item_type: str
	item_title: str
	source_doctype: str
	source_name: str
	source_owner: str | None
	executive_sponsor: str | None
	priority_score: float
	priority_band: str
	urgency_bucket: str
	source_link_integrity_confirmed: int
	read_only_confirmed: int
	non_duplication_boundary_confirmed: int
	ranking_rationale: str
	perf_max_ranking_execution_duration: str
	perf_min_items_per_review_window: str
	perf_ordering_stability_tolerance: str
	perf_supported_ranking_dataset_profile: str
	perf_degradation_policy_on_capacity_exceeded: str
	perf_supported_review_window_definition: str

	def as_dict(self) -> dict[str, Any]:
		return {
			"lighthouse_workflow_charter": self.lighthouse_workflow_charter,
			"decision_record": self.decision_record,
			"review_window_start": self.review_window_start,
			"review_window_end": self.review_window_end,
			"policy_version": self.policy_version,
			"item_type": self.item_type,
			"item_title": self.item_title,
			"source_doctype": self.source_doctype,
			"source_name": self.source_name,
			"source_owner": self.source_owner or "",
			"executive_sponsor": self.executive_sponsor or "",
			"priority_score": self.priority_score,
			"priority_band": self.priority_band,
			"urgency_bucket": self.urgency_bucket,
			"source_link_integrity_confirmed": self.source_link_integrity_confirmed,
			"read_only_confirmed": self.read_only_confirmed,
			"non_duplication_boundary_confirmed": self.non_duplication_boundary_confirmed,
			"ranking_rationale": self.ranking_rationale,
			"perf_max_ranking_execution_duration": self.perf_max_ranking_execution_duration,
			"perf_min_items_per_review_window": self.perf_min_items_per_review_window,
			"perf_ordering_stability_tolerance": self.perf_ordering_stability_tolerance,
			"perf_supported_ranking_dataset_profile": self.perf_supported_ranking_dataset_profile,
			"perf_degradation_policy_on_capacity_exceeded": self.perf_degradation_policy_on_capacity_exceeded,
			"perf_supported_review_window_definition": self.perf_supported_review_window_definition,
		}


def evaluate_feature2_prioritization(
	*,
	lighthouse_workflow_charter: str,
	review_window_start: str,
	review_window_end: str,
	policy_version: str,
	decision_record: str | None = None,
	acceptance_parameters: dict[str, Any] | None = None,
	invocation_context: str = "direct_helper_call",
) -> tuple[Feature2FollowThroughItem, ...]:
	_require_governance_role()
	_require_read_permissions()
	_enforce_no_unresolved_baseline_change_triggers()

	window_start, window_end = _validate_review_window(review_window_start, review_window_end)
	policy_version_text = _normalize_required_text(policy_version, "Policy Version")
	parameters = _resolve_acceptance_parameters(acceptance_parameters)

	decision_docs = _fetch_decision_docs(lighthouse_workflow_charter, decision_record)
	items: list[Feature2FollowThroughItem] = []
	for decision in decision_docs:
		items.extend(
			_build_decision_items(
				decision=decision,
				window_start=window_start,
				window_end=window_end,
				policy_version=policy_version_text,
				parameters=parameters,
			)
		)

	sorted_items = tuple(sorted(items, key=_priority_sort_key))
	_enforce_source_link_integrity(sorted_items)
	_enforce_orv_eps_non_duplication_boundary(sorted_items)
	_record_actor_trace_audit_evidence(
		invocation_context=invocation_context,
		lighthouse_workflow_charter=lighthouse_workflow_charter,
		decision_record=decision_record,
		review_window_start=window_start,
		review_window_end=window_end,
		policy_version=policy_version_text,
		acceptance_parameters=parameters,
		items=sorted_items,
	)
	return sorted_items


def _build_decision_items(
	*,
	decision: Any,
	window_start: date,
	window_end: date,
	policy_version: str,
	parameters: Feature2AcceptanceParameters,
) -> list[Feature2FollowThroughItem]:
	items: list[Feature2FollowThroughItem] = []

	if _should_include_decision_item(decision):
		score, urgency_bucket, reason = _score_decision_item(decision)
		items.append(
			_build_item(
				decision=decision,
				item_type="Decision Approval Readiness",
				item_title=f"Decision {decision.name} is not approved",
				source_doctype="Decision Record",
				source_name=decision.name,
				priority_score=score,
				urgency_bucket=urgency_bucket,
				ranking_rationale=reason,
				window_start=window_start,
				window_end=window_end,
				policy_version=policy_version,
				parameters=parameters,
			)
		)

	dependency_records = frappe.get_list(
		"Dependency Exception Record",
		filters={"decision_record": decision.name},
		fields=[
			"name",
			"dependency_title",
			"dependency_status",
			"dependency_criticality",
			"target_resolution_date",
			"exception_required",
			"accountable_owner",
			"executive_sponsor",
		],
	)
	for dependency in dependency_records:
		if not _is_within_window(dependency.get("target_resolution_date"), window_start, window_end):
			continue
		if not _should_include_dependency_item(dependency):
			continue

		score, urgency_bucket, reason = _score_dependency_item(dependency)
		items.append(
			_build_item(
				decision=decision,
				item_type="Dependency Risk",
				item_title=dependency.get("dependency_title") or dependency.get("name"),
				source_doctype="Dependency Exception Record",
				source_name=dependency.get("name"),
				source_owner=dependency.get("accountable_owner"),
				executive_sponsor=dependency.get("executive_sponsor"),
				priority_score=score,
				urgency_bucket=urgency_bucket,
				ranking_rationale=reason,
				window_start=window_start,
				window_end=window_end,
				policy_version=policy_version,
				parameters=parameters,
			)
		)

	attribution_records = frappe.get_list(
		"Attribution Case",
		filters={"decision_record": decision.name},
		fields=[
			"name",
			"attribution_title",
			"approval_state",
			"confidence_score",
			"observation_end_date",
			"accountable_owner",
			"executive_sponsor",
		],
	)
	for attribution in attribution_records:
		if not _is_within_window(attribution.get("observation_end_date"), window_start, window_end):
			continue
		if not _should_include_attribution_item(attribution):
			continue

		score, urgency_bucket, reason = _score_attribution_item(attribution)
		items.append(
			_build_item(
				decision=decision,
				item_type="Attribution Confidence",
				item_title=attribution.get("attribution_title") or attribution.get("name"),
				source_doctype="Attribution Case",
				source_name=attribution.get("name"),
				source_owner=attribution.get("accountable_owner"),
				executive_sponsor=attribution.get("executive_sponsor"),
				priority_score=score,
				urgency_bucket=urgency_bucket,
				ranking_rationale=reason,
				window_start=window_start,
				window_end=window_end,
				policy_version=policy_version,
				parameters=parameters,
			)
		)

	return items


def _build_item(
	*,
	decision: Any,
	item_type: str,
	item_title: str,
	source_doctype: str,
	source_name: str,
	priority_score: float,
	urgency_bucket: str,
	ranking_rationale: str,
	window_start: date,
	window_end: date,
	policy_version: str,
	parameters: Feature2AcceptanceParameters,
	source_owner: str | None = None,
	executive_sponsor: str | None = None,
) -> Feature2FollowThroughItem:
	priority_band = _derive_priority_band(priority_score)
	non_duplication_boundary_confirmed = _compute_non_duplication_boundary_confirmation(
		item_type=item_type,
		source_doctype=source_doctype,
	)
	source_link_integrity_confirmed = _confirm_source_link_integrity(
		source_doctype=source_doctype,
		source_name=source_name,
		decision_name=decision.get("name"),
		charter_name=decision.get("lighthouse_workflow_charter"),
	)
	return Feature2FollowThroughItem(
		lighthouse_workflow_charter=decision.get("lighthouse_workflow_charter"),
		decision_record=decision.get("name"),
		review_window_start=window_start.isoformat(),
		review_window_end=window_end.isoformat(),
		policy_version=policy_version,
		item_type=item_type,
		item_title=item_title,
		source_doctype=source_doctype,
		source_name=source_name,
		source_owner=source_owner or decision.get("accountable_owner"),
		executive_sponsor=executive_sponsor or decision.get("executive_sponsor"),
		priority_score=round(priority_score, 2),
		priority_band=priority_band,
		urgency_bucket=urgency_bucket,
		source_link_integrity_confirmed=source_link_integrity_confirmed,
		read_only_confirmed=1,
		non_duplication_boundary_confirmed=non_duplication_boundary_confirmed,
		ranking_rationale=ranking_rationale,
		perf_max_ranking_execution_duration=parameters.perf_max_ranking_execution_duration,
		perf_min_items_per_review_window=parameters.perf_min_items_per_review_window,
		perf_ordering_stability_tolerance=parameters.perf_ordering_stability_tolerance,
		perf_supported_ranking_dataset_profile=parameters.perf_supported_ranking_dataset_profile,
		perf_degradation_policy_on_capacity_exceeded=parameters.perf_degradation_policy_on_capacity_exceeded,
		perf_supported_review_window_definition=parameters.perf_supported_review_window_definition,
	)


def _confirm_source_link_integrity(
	*,
	source_doctype: str,
	source_name: str,
	decision_name: str,
	charter_name: str,
) -> int:
	if not source_doctype or not source_name:
		return 0
	if not frappe.db.exists(source_doctype, source_name):
		return 0

	if source_doctype == "Decision Record":
		row = frappe.db.get_value(
			"Decision Record",
			source_name,
			["name", "lighthouse_workflow_charter"],
			as_dict=True,
		)
		return 1 if row and row.name == decision_name and row.lighthouse_workflow_charter == charter_name else 0

	if source_doctype == "Dependency Exception Record":
		row = frappe.db.get_value(
			"Dependency Exception Record",
			source_name,
			["decision_record", "lighthouse_workflow_charter"],
			as_dict=True,
		)
		return 1 if row and row.decision_record == decision_name and row.lighthouse_workflow_charter == charter_name else 0

	if source_doctype == "Attribution Case":
		row = frappe.db.get_value(
			"Attribution Case",
			source_name,
			["decision_record", "lighthouse_workflow_charter"],
			as_dict=True,
		)
		return 1 if row and row.decision_record == decision_name and row.lighthouse_workflow_charter == charter_name else 0

	return 0


def _enforce_source_link_integrity(items: tuple[Feature2FollowThroughItem, ...]) -> None:
	violations: list[str] = []
	for item in items:
		if item.source_link_integrity_confirmed != 1:
			violations.append(f"{item.source_doctype}:{item.source_name}")

	if violations:
		frappe.throw(
			_("Feature 2 source-link integrity validation failed for: {0}.").format(", ".join(sorted(violations))),
			exc=frappe.ValidationError,
		)


def _record_actor_trace_audit_evidence(
	*,
	invocation_context: str,
	lighthouse_workflow_charter: str,
	decision_record: str | None,
	review_window_start: date,
	review_window_end: date,
	policy_version: str,
	acceptance_parameters: Feature2AcceptanceParameters,
	items: tuple[Feature2FollowThroughItem, ...],
) -> None:
	payload = {
		"event": "feature2_prioritization_review_executed",
		"actor": frappe.session.user,
		"executed_at": now_datetime().isoformat(),
		"report_invocation_context": invocation_context,
		"governance_review_context": {
			"policy_version": policy_version,
			"acceptance_parameters": acceptance_parameters.as_dict(),
		},
		"requested_review_window": {
			"start": review_window_start.isoformat(),
			"end": review_window_end.isoformat(),
		},
		"source_charter": lighthouse_workflow_charter,
		"decision_record": decision_record or "",
		"result_count": len(items),
	}
	frappe.logger(FEATURE2_AUDIT_LOGGER_NAME).info(payload)


def _compute_non_duplication_boundary_confirmation(*, item_type: str, source_doctype: str) -> int:
	if item_type not in ALLOWED_ITEM_TYPES:
		return 0
	if source_doctype in PROHIBITED_NON_DUPLICATION_SOURCES:
		return 0
	if source_doctype not in ALLOWED_SOURCE_DOCTYPES:
		return 0
	return 1


def _enforce_orv_eps_non_duplication_boundary(items: tuple[Feature2FollowThroughItem, ...]) -> None:
	violations: list[str] = []
	for item in items:
		if item.non_duplication_boundary_confirmed != 1:
			violations.append(f"{item.source_doctype}:{item.source_name}")

	if violations:
		frappe.throw(
			_("Feature 2 ORV/EPS non-duplication boundary could not be confirmed for: {0}.").format(
				", ".join(sorted(violations))
			),
			exc=frappe.ValidationError,
		)


def _score_decision_item(decision: Any) -> tuple[float, str, str]:
	urgency_score, urgency_bucket = _urgency_from_date(decision.get("target_decision_date"))
	base = PRIORITY_TYPE_BASE_WEIGHT["Decision Approval Readiness"]
	score = base + urgency_score
	reason = _(
		"Decision approval readiness item derived from non-approved decision state and target date urgency."
	)
	return score, urgency_bucket, reason


def _score_dependency_item(dependency: Any) -> tuple[float, str, str]:
	urgency_score, urgency_bucket = _urgency_from_date(dependency.get("target_resolution_date"))
	criticality = dependency.get("dependency_criticality") or "Low"
	criticality_score = DEPENDENCY_CRITICALITY_WEIGHT.get(criticality, 0.0)
	exception_bonus = 10.0 if cint(dependency.get("exception_required")) else 0.0
	base = PRIORITY_TYPE_BASE_WEIGHT["Dependency Risk"]
	score = base + criticality_score + urgency_score + exception_bonus
	reason = _(
		"Dependency risk item derived from unresolved dependency status, criticality, exception requirement, and target-date urgency."
	)
	return score, urgency_bucket, reason


def _score_attribution_item(attribution: Any) -> tuple[float, str, str]:
	urgency_score, urgency_bucket = _urgency_from_date(attribution.get("observation_end_date"))
	confidence = flt(attribution.get("confidence_score") or 0)
	confidence_gap = max(0.0, ATTRIBUTION_CONFIDENCE_THRESHOLD - confidence)
	confidence_score = round(confidence_gap * 100, 2)
	state_bonus = 15.0 if attribution.get("approval_state") != APPROVED_STATE else 0.0
	base = PRIORITY_TYPE_BASE_WEIGHT["Attribution Confidence"]
	score = base + urgency_score + confidence_score + state_bonus
	reason = _(
		"Attribution confidence item derived from approval state, confidence-gap threshold, and observation-window urgency."
	)
	return score, urgency_bucket, reason


def _urgency_from_date(value: Any) -> tuple[float, str]:
	if not value:
		return 0.0, "No date"

	target_date = getdate(value)
	today = getdate(nowdate())
	delta_days = (target_date - today).days
	if delta_days < 0:
		return 30.0, "Overdue"
	if delta_days <= 7:
		return 20.0, "Due within 7 days"
	if delta_days <= 30:
		return 10.0, "Due within 30 days"
	return 0.0, "Beyond 30 days"


def _derive_priority_band(priority_score: float) -> str:
	for band, minimum in PRIORITY_BAND_BY_MIN_SCORE:
		if priority_score >= minimum:
			return band
	return "Low"


def _priority_sort_key(item: Feature2FollowThroughItem) -> tuple[Any, ...]:
	band_rank = {
		"Critical": 0,
		"High": 1,
		"Medium": 2,
		"Low": 3,
	}.get(item.priority_band, 99)
	return (
		-item.priority_score,
		band_rank,
		SOURCE_DOCTYPE_RANK.get(item.source_doctype, 99),
		item.source_name,
		item.item_type,
	)


def _should_include_decision_item(decision: Any) -> bool:
	return decision.get("approval_state") != APPROVED_STATE


def _should_include_dependency_item(dependency: dict[str, Any]) -> bool:
	status = dependency.get("dependency_status")
	if status == RESOLVED_STATUS:
		return False
	criticality = dependency.get("dependency_criticality")
	return criticality in HIGH_OR_CRITICAL or cint(dependency.get("exception_required")) == 1


def _should_include_attribution_item(attribution: dict[str, Any]) -> bool:
	if attribution.get("approval_state") != APPROVED_STATE:
		return True
	confidence = flt(attribution.get("confidence_score") or 0)
	return confidence < ATTRIBUTION_CONFIDENCE_THRESHOLD


def _is_within_window(value: Any, window_start: date, window_end: date) -> bool:
	if not value:
		return True
	current = getdate(value)
	return window_start <= current <= window_end


def _fetch_decision_docs(lighthouse_workflow_charter: str, decision_record: str | None) -> tuple[dict[str, Any], ...]:
	filters = {"lighthouse_workflow_charter": lighthouse_workflow_charter}
	if decision_record:
		filters["name"] = decision_record

	rows = frappe.get_list(
		"Decision Record",
		filters=filters,
		fields=[
			"name",
			"lighthouse_workflow_charter",
			"decision_title",
			"approval_state",
			"decision_criticality",
			"target_decision_date",
			"accountable_owner",
			"executive_sponsor",
		],
	)
	if decision_record and not rows:
		frappe.throw(_("Decision Record {0} was not found for the selected charter.").format(decision_record))
	return tuple(rows)


def _enforce_no_unresolved_baseline_change_triggers() -> None:
	migration_triggers = _evaluate_migration_triggers()
	unresolved = tuple(sorted(trigger for trigger, active in migration_triggers.items() if active))
	if unresolved:
		frappe.throw(
			_("Feature 2 blocked due to unresolved Baseline Change triggers: {0}.").format(", ".join(unresolved)),
			exc=frappe.ValidationError,
		)


def _evaluate_migration_triggers() -> dict[str, bool]:
	return {
		"duplicate_source_of_truth_persistence_risk": _detect_duplicate_source_of_truth_persistence_risk(),
		"ownership_mapping_mutation_risk": _detect_ownership_mapping_mutation_risk(),
		"runtime_contract_mutation_risk": _detect_runtime_contract_mutation_risk(),
	}


def _detect_duplicate_source_of_truth_persistence_risk() -> bool:
	for doctype_name in PROHIBITED_DUPLICATE_PERSISTENCE_DOCTYPES:
		if frappe.db.exists("DocType", doctype_name):
			return True
	return False


def _detect_ownership_mapping_mutation_risk() -> bool:
	if not frappe.db.exists("Report", FEATURE2_REPORT_NAME):
		return True

	report_roles = set(
		frappe.get_all(
			"Has Role",
			filters={"parent": FEATURE2_REPORT_NAME, "parenttype": "Report", "parentfield": "roles"},
			pluck="role",
		)
	)
	return report_roles != set(GOVERNANCE_ROLES)


def _detect_runtime_contract_mutation_risk() -> bool:
	report_row = frappe.db.get_value(
		"Report",
		FEATURE2_REPORT_NAME,
		["report_type", "is_standard", "module", "ref_doctype"],
		as_dict=True,
	)
	if not report_row:
		return True

	if report_row.report_type != "Script Report":
		return True
	if report_row.is_standard != "Yes":
		return True
	if report_row.module != FEATURE2_REPORT_MODULE:
		return True
	if report_row.ref_doctype != FEATURE2_REPORT_REF_DOCTYPE:
		return True
	return False


def _validate_review_window(review_window_start: str, review_window_end: str) -> tuple[date, date]:
	start_text = _normalize_required_text(review_window_start, "Review Window Start")
	end_text = _normalize_required_text(review_window_end, "Review Window End")
	start = getdate(start_text)
	end = getdate(end_text)
	if start > end:
		frappe.throw(_("Review Window Start cannot be after Review Window End."), exc=frappe.ValidationError)
	return start, end


def _normalize_required_text(value: Any, field_label: str) -> str:
	text = str(value or "").strip()
	if not text:
		frappe.throw(_("{0} is required.").format(field_label), exc=frappe.ValidationError)
	return text


def _resolve_acceptance_parameters(value: dict[str, Any] | None) -> Feature2AcceptanceParameters:
	params = dict(value or {})
	approval_metadata = params.get("approval_metadata")

	resolved = {
		"perf_max_ranking_execution_duration": _normalize_required_text(
			params.get(
				"perf_max_ranking_execution_duration",
				PERF_PARAMETER_DEFAULTS["perf_max_ranking_execution_duration"],
			),
			"PERF_MAX_RANKING_EXECUTION_DURATION",
		),
		"perf_min_items_per_review_window": _normalize_required_text(
			params.get("perf_min_items_per_review_window", PERF_PARAMETER_DEFAULTS["perf_min_items_per_review_window"]),
			"PERF_MIN_ITEMS_PER_REVIEW_WINDOW",
		),
		"perf_ordering_stability_tolerance": _normalize_required_text(
			params.get(
				"perf_ordering_stability_tolerance",
				PERF_PARAMETER_DEFAULTS["perf_ordering_stability_tolerance"],
			),
			"PERF_ORDERING_STABILITY_TOLERANCE",
		),
		"perf_supported_ranking_dataset_profile": _normalize_required_text(
			params.get(
				"perf_supported_ranking_dataset_profile",
				PERF_PARAMETER_DEFAULTS["perf_supported_ranking_dataset_profile"],
			),
			"PERF_SUPPORTED_RANKING_DATASET_PROFILE",
		),
		"perf_degradation_policy_on_capacity_exceeded": _normalize_required_text(
			params.get(
				"perf_degradation_policy_on_capacity_exceeded",
				PERF_PARAMETER_DEFAULTS["perf_degradation_policy_on_capacity_exceeded"],
			),
			"PERF_DEGRADATION_POLICY_ON_CAPACITY_EXCEEDED",
		),
		"perf_supported_review_window_definition": _normalize_required_text(
			params.get(
				"perf_supported_review_window_definition",
				PERF_PARAMETER_DEFAULTS["perf_supported_review_window_definition"],
			),
			"PERF_SUPPORTED_REVIEW_WINDOW_DEFINITION",
		),
	}

	uses_custom_acceptance_parameters = any(
		resolved[key] != PERF_PARAMETER_DEFAULTS[key] for key in PERF_PARAMETER_DEFAULTS
	)
	if uses_custom_acceptance_parameters:
		_validate_acceptance_parameter_approval_metadata(approval_metadata)

	return Feature2AcceptanceParameters(
		perf_max_ranking_execution_duration=resolved["perf_max_ranking_execution_duration"],
		perf_min_items_per_review_window=resolved["perf_min_items_per_review_window"],
		perf_ordering_stability_tolerance=resolved["perf_ordering_stability_tolerance"],
		perf_supported_ranking_dataset_profile=resolved["perf_supported_ranking_dataset_profile"],
		perf_degradation_policy_on_capacity_exceeded=resolved["perf_degradation_policy_on_capacity_exceeded"],
		perf_supported_review_window_definition=resolved["perf_supported_review_window_definition"],
	)


def _validate_acceptance_parameter_approval_metadata(value: Any) -> None:
	if not isinstance(value, dict):
		frappe.throw(
			_("Custom acceptance parameters require approval_metadata."),
			exc=frappe.ValidationError,
		)

	for key in REQUIRED_APPROVAL_METADATA_KEYS:
		text = str(value.get(key) or "").strip()
		if not text:
			frappe.throw(
				_("approval_metadata.{0} is required for custom acceptance parameters.").format(key),
				exc=frappe.ValidationError,
			)

	if str(value.get("approval_status") or "").strip().lower() != "approved":
		frappe.throw(
			_("approval_metadata.approval_status must be 'Approved' for custom acceptance parameters."),
			exc=frappe.ValidationError,
		)


def _require_governance_role() -> None:
	roles = set(frappe.get_roles())
	if not roles.intersection(GOVERNANCE_ROLES):
		frappe.throw(
			_("Feature 2 Follow-Through Prioritization Review requires a governance role."),
			exc=frappe.PermissionError,
		)


def _require_read_permissions() -> None:
	for doctype in (
		"Lighthouse Workflow Charter",
		"Decision Record",
		"Dependency Exception Record",
		"Attribution Case",
	):
		frappe.has_permission(doctype, ptype="read", throw=True)


__all__ = [
	"Feature2AcceptanceParameters",
	"Feature2FollowThroughItem",
	"evaluate_feature2_prioritization",
]
