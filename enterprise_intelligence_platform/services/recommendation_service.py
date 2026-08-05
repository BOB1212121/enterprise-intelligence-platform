"""RecommendationService — owns all database writes for AI recommendations.

Responsibilities:
  - Re-validate recommendation schema before any DB write.
  - Build and insert Decision Record (with Assumption rows).
  - Build and insert AI Decision Reasoning Trace.
  - Enforce idempotency via source_recommendation_hash.
  - Provide atomic commit/rollback around the two inserts.

Forbidden here:
  - Permission checks     (API layer's responsibility)
  - Input parsing         (API layer's responsibility)
  - AI reasoning
  - Read operations beyond the charter executive-sponsor lookup
"""
from __future__ import annotations

import hashlib
import json

import frappe
from frappe.utils import today as frappe_today

from enterprise_intelligence_platform.ai_agent.schemas import (
    Recommendation,
    recommendation_from_dict,
)

# ── DocType names ─────────────────────────────────────────────────────────────

_TRACE_DT = "AI Decision Reasoning Trace"
_REJECTION_DT = "AI Recommendation Rejection Log"
_CHARTER_DT = "Lighthouse Workflow Charter"
_DECISION_DT = "Decision Record"

# ── Module-level helpers (no side effects) ────────────────────────────────────


def _compute_hash(charter_name: str, recommendation_index: int, execution_timestamp: str) -> str:
    """SHA-256 idempotency key for one recommendation acceptance."""
    raw = f"{charter_name}:{recommendation_index}:{execution_timestamp}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _map_decision_type(recommendation_class: str) -> str:
    return "Strategic" if recommendation_class == "Learning-Oriented" else "Operational"


def _map_criticality(confidence_band: str) -> str:
    return confidence_band if confidence_band in ("High", "Medium", "Low") else "Medium"


# ── Service ───────────────────────────────────────────────────────────────────


class RecommendationService:
    """Service layer for persisting AI recommendation decisions.

    The API layer must call frappe.has_permission() before invoking this class.
    This class assumes the caller has already verified permissions.
    """

    def accept(self, charter_name: str, recommendation_data: dict) -> dict[str, str]:
        """Persist an accepted recommendation as a governed Decision Record.

        Returns {"decision_record": name, "trace_record": name}.
        Idempotent: if a trace with the same hash already exists, returns the
        existing names without creating duplicates.
        """
        recommendation = self._validate_recommendation(recommendation_data)

        model_identifier = str(recommendation_data.get("model_identifier") or "unknown")
        fallback_used = bool(recommendation_data.get("fallback_used", False))
        execution_timestamp = str(recommendation_data.get("execution_timestamp") or "")
        context_snapshot_str = json.dumps(recommendation_data.get("context_snapshot") or {})

        hash_value = _compute_hash(charter_name, recommendation.index, execution_timestamp)

        # Fast path: already accepted (idempotency / retry / double-click)
        existing = self._find_existing_trace(hash_value)
        if existing:
            return {
                "decision_record": existing["decision_record"],
                "trace_record": existing["name"],
            }

        executive_sponsor = (
            frappe.db.get_value(_CHARTER_DT, charter_name, "executive_sponsor") or ""
        )
        dr_doc = self._build_decision_record(charter_name, recommendation, executive_sponsor)

        try:
            dr_doc.insert(ignore_permissions=False)
            trace_doc = self._build_trace_doc(
                charter_name=charter_name,
                decision_record_name=dr_doc.name,
                hash_value=hash_value,
                recommendation=recommendation,
                model_identifier=model_identifier,
                fallback_used=fallback_used,
                execution_timestamp=execution_timestamp,
                context_snapshot_str=context_snapshot_str,
            )
            trace_doc.insert(ignore_permissions=True)
            frappe.db.commit()
            return {"decision_record": dr_doc.name, "trace_record": trace_doc.name}
        except frappe.UniqueValidationError:
            # Race condition: concurrent accept with same hash won the race
            frappe.db.rollback()
            existing = self._find_existing_trace(hash_value)
            if existing:
                return {
                    "decision_record": existing["decision_record"],
                    "trace_record": existing["name"],
                }
            raise
        except Exception:
            frappe.db.rollback()
            raise

    def reject(self, charter_name: str, recommendation_data: dict, reason: str) -> dict[str, str]:
        """Record a human rejection of an AI recommendation.

        Returns {"rejection_log": name}.
        """
        recommendation = self._validate_recommendation(recommendation_data)

        if not (reason or "").strip():
            frappe.throw("Rejection reason is required.", frappe.ValidationError)

        log_doc = frappe.get_doc({
            "doctype": _REJECTION_DT,
            "naming_series": "ARRL-.YYYY.-.#####",
            "charter": charter_name,
            "rejected_by": frappe.session.user,
            "rejected_at": frappe.utils.now_datetime(),
            "reason": reason.strip(),
            "recommendation_class": recommendation.recommendation_class,
            "recommendation_summary": recommendation.objective_served[:140],
            "recommendation_data": json.dumps(recommendation_data),
        })
        log_doc.insert(ignore_permissions=False)
        frappe.db.commit()
        return {"rejection_log": log_doc.name}

    # ── private helpers ───────────────────────────────────────────────────────

    def _validate_recommendation(self, recommendation_data: dict) -> Recommendation:
        """Re-validate schema; throws frappe.ValidationError on failure."""
        try:
            return recommendation_from_dict(recommendation_data)
        except (KeyError, ValueError, TypeError) as exc:
            frappe.throw(f"Invalid recommendation payload: {exc}", frappe.ValidationError)

    def _find_existing_trace(self, hash_value: str) -> dict | None:
        rows = frappe.get_all(
            _TRACE_DT,
            filters={"source_recommendation_hash": hash_value},
            fields=["name", "decision_record"],
            limit=1,
        )
        return rows[0] if rows else None

    def _build_decision_record(
        self,
        charter_name: str,
        recommendation: Recommendation,
        executive_sponsor: str,
    ):
        today = frappe_today()
        trade_off_text = (
            "; ".join(recommendation.trade_offs)
            if recommendation.trade_offs
            else "No explicit trade-offs identified"
        )
        return frappe.get_doc({
            "doctype": _DECISION_DT,
            "naming_series": "DR-.YYYY.-.#####",
            "decision_title": recommendation.objective_served[:140],
            "lighthouse_workflow_charter": charter_name,
            "accountable_owner": frappe.session.user,
            "executive_sponsor": executive_sponsor,
            "decision_type": _map_decision_type(recommendation.recommendation_class),
            "decision_criticality": _map_criticality(recommendation.confidence_state.band),
            "proposal_date": today,
            "target_decision_date": frappe.utils.add_days(today, 14),
            "business_decision_summary": recommendation.expected_value_hypothesis[:500],
            "tradeoff_summary": trade_off_text[:500],
            "assumptions": [
                {
                    "assumption_text": a,
                    "confidence_score": 0.5,
                    "falsifiability_note": "",
                    "expiry_date": None,
                }
                for a in recommendation.assumptions
            ],
        })

    def _build_trace_doc(
        self,
        charter_name: str,
        decision_record_name: str,
        hash_value: str,
        recommendation: Recommendation,
        model_identifier: str,
        fallback_used: bool,
        execution_timestamp: str,
        context_snapshot_str: str,
    ):
        return frappe.get_doc({
            "doctype": _TRACE_DT,
            "naming_series": "ADRT-.YYYY.-.#####",
            "charter": charter_name,
            "decision_record": decision_record_name,
            "model_identifier": model_identifier,
            "fallback_used": 1 if fallback_used else 0,
            "execution_timestamp": execution_timestamp,
            "recommendation_class": recommendation.recommendation_class,
            "recommendation_index": recommendation.index,
            "source_recommendation_hash": hash_value,
            "context_snapshot": context_snapshot_str,
            "confidence_rationale": recommendation.confidence_state.rationale,
        })


__all__ = ["RecommendationService", "_compute_hash"]
