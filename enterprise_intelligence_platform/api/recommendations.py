"""AI recommendation API endpoints.

Intentionally thin: permission → parse → validate → delegate.
No business logic, no reasoning, no DB writes in this module.

Whitelisted methods are exposed as:
  enterprise_intelligence_platform.api.recommendations.<method>
"""
from __future__ import annotations

import json

import frappe

from enterprise_intelligence_platform.ai_agent.agent import ReasoningAgent
from enterprise_intelligence_platform.ai_agent.schemas import recommendation_from_dict
from enterprise_intelligence_platform.integration.erpnext_context_reader import ERPNextContextReader
from enterprise_intelligence_platform.services.recommendation_service import RecommendationService

_CHARTER_DOCTYPE = "Lighthouse Workflow Charter"
_ACCEPTED_STATE = "Baseline Accepted"


@frappe.whitelist()
def get_ai_recommendations(charter_name: str) -> dict:
    """Read charter context, generate AI recommendations, return serialised package.

    Caller must have Read on Lighthouse Workflow Charter.
    Charter must be in Baseline Accepted state.
    """
    frappe.has_permission(_CHARTER_DOCTYPE, "read", charter_name, throw=True)

    approval_state = frappe.db.get_value(_CHARTER_DOCTYPE, charter_name, "approval_state")
    if approval_state is None:
        frappe.throw(
            f"Lighthouse Workflow Charter {charter_name!r} not found.",
            frappe.DoesNotExistError,
        )
    if approval_state != _ACCEPTED_STATE:
        frappe.throw(
            f"Charter must be in {_ACCEPTED_STATE!r} state (current: {approval_state!r}).",
            frappe.ValidationError,
        )

    context = ERPNextContextReader().read(charter_name)
    package = ReasoningAgent().generate(context)
    return package.to_api_dict()


@frappe.whitelist()
def accept_recommendation(charter_name: str, recommendation_data: str) -> dict:
    """Accept one AI recommendation, creating a governed Decision Record.

    Caller must have Create on Decision Record.
    Returns {"decision_record": name, "trace_record": name}.
    Idempotent: repeated calls with identical payload return the same result.
    """
    frappe.has_permission("Decision Record", "create", throw=True)

    data = _parse_json(recommendation_data)
    _validate_schema(data)

    return RecommendationService().accept(charter_name, data)


@frappe.whitelist()
def reject_recommendation(charter_name: str, recommendation_data: str, reason: str) -> dict:
    """Reject one AI recommendation, recording the decision in an audit log.

    Caller must have Read on Lighthouse Workflow Charter.
    Returns {"rejection_log": name}.
    """
    frappe.has_permission(_CHARTER_DOCTYPE, "read", charter_name, throw=True)

    data = _parse_json(recommendation_data)
    _validate_schema(data)

    if not (reason or "").strip():
        frappe.throw("Rejection reason must not be empty.", frappe.ValidationError)

    return RecommendationService().reject(charter_name, data, reason)


# ── private helpers ───────────────────────────────────────────────────────────


def _parse_json(raw: str) -> dict:
    """Deserialise raw JSON string. Calls frappe.throw on any parse failure."""
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        frappe.throw(f"Invalid JSON in recommendation_data: {exc}", frappe.ValidationError)


def _validate_schema(data: dict) -> None:
    """Verify dict satisfies the Recommendation schema. Calls frappe.throw on failure."""
    try:
        recommendation_from_dict(data)
    except (KeyError, ValueError, TypeError) as exc:
        frappe.throw(f"Invalid recommendation schema: {exc}", frappe.ValidationError)
