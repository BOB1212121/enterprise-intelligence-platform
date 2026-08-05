"""Tests for RecommendationService.

All frappe DB/doc calls are mocked so no Frappe site context is required.

Run with:  python -m pytest enterprise_intelligence_platform/tests/test_recommendation_service.py -v
"""
from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any
from unittest.mock import MagicMock, patch, call

import pytest

import frappe as _frappe_module

from enterprise_intelligence_platform.ai_agent.schemas import (
    REQUIRED_CONFIDENCE_DIMENSIONS,
    recommendation_to_dict,
)
from enterprise_intelligence_platform.ai_agent.engine.null_engine import NullEngine
from enterprise_intelligence_platform.ai_agent.agent import ReasoningAgent
from enterprise_intelligence_platform.ai_agent.schemas import (
    CanonicalDecisionSignal,
    CanonicalDependencySignal,
    CanonicalKPISignal,
    CanonicalActionSignal,
    CharterContext,
)
from enterprise_intelligence_platform.services.recommendation_service import (
    RecommendationService,
    _compute_hash,
    _map_decision_type,
    _map_criticality,
)

_SERVICE = "enterprise_intelligence_platform.services.recommendation_service"

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _rich_context() -> CharterContext:
    return CharterContext(
        charter_name="LWC-2026-00001",
        business_objective="Reduce DRR below 8%",
        in_scope_definition="Q3 operational decisions",
        open_decisions=(
            CanonicalDecisionSignal(
                name="DR-001", state="Draft", criticality="High",
                decision_type="Operational", owner="alice@example.com",
            ),
        ),
        open_dependencies=(
            CanonicalDependencySignal(
                name="DER-001", criticality="Critical", status="At Risk",
                dependency_type="System", days_overdue=5,
            ),
        ),
        kpi_signals=(CanonicalKPISignal(kpi_code="DRR", baseline_value=12.0, data_source="ERP"),),
        overdue_actions=(CanonicalActionSignal(name="TASK-001", overdue_days=3, owner="alice@example.com"),),
    )


def _make_recommendation_data() -> dict[str, Any]:
    """Build a valid accept payload by running a real pipeline."""
    pkg = ReasoningAgent(engine=NullEngine()).generate(_rich_context())
    rec = pkg.recommendations[0]
    data = recommendation_to_dict(rec)
    data["model_identifier"] = pkg.model_identifier
    data["fallback_used"] = pkg.fallback_used
    data["execution_timestamp"] = pkg.execution_timestamp
    data["context_snapshot"] = pkg.context_snapshot
    return data


@contextmanager
def _mock_service(
    existing_trace: dict | None = None,
    dr_name: str = "DR-2026-00042",
    trace_name: str = "ADRT-2026-00001",
    rej_name: str = "ARRL-2026-00001",
    executive_sponsor: str = "exec@example.com",
    raise_on_trace_insert: Exception | None = None,
):
    """Patch frappe for one service call."""
    with patch(f"{_SERVICE}.frappe") as mock_f:
        mock_f.session.user = "alice@example.com"
        mock_f.db.get_value.return_value = executive_sponsor
        mock_f.ValidationError = _frappe_module.ValidationError
        mock_f.UniqueValidationError = _frappe_module.UniqueValidationError
        # mirror real frappe.throw() which always raises
        mock_f.throw.side_effect = lambda msg, exc=None, *a, **kw: (_ for _ in ()).throw(
            (exc or Exception)(msg)
        )

        dr_doc = MagicMock()
        dr_doc.name = dr_name

        trace_doc = MagicMock()
        trace_doc.name = trace_name
        if raise_on_trace_insert:
            trace_doc.insert.side_effect = raise_on_trace_insert

        rej_doc = MagicMock()
        rej_doc.name = rej_name

        def fake_get_doc(data_dict: dict) -> MagicMock:
            dt = data_dict.get("doctype", "")
            if dt == "Decision Record":
                # copy dict data onto mock so tests can inspect field values
                for k, v in data_dict.items():
                    if k != "doctype":
                        setattr(dr_doc, k, v)
                return dr_doc
            if dt == "AI Decision Reasoning Trace":
                for k, v in data_dict.items():
                    if k != "doctype":
                        setattr(trace_doc, k, v)
                return trace_doc
            if dt == "AI Recommendation Rejection Log":
                for k, v in data_dict.items():
                    if k != "doctype":
                        setattr(rej_doc, k, v)
                return rej_doc
            return MagicMock()

        mock_f.get_doc.side_effect = fake_get_doc

        if existing_trace:
            mock_f.get_all.return_value = [existing_trace]
        else:
            mock_f.get_all.return_value = []

        with patch(f"{_SERVICE}.frappe_today", return_value="2026-08-05"):
            yield mock_f, dr_doc, trace_doc, rej_doc


# ── _compute_hash ─────────────────────────────────────────────────────────────


def test_compute_hash_is_deterministic() -> None:
    h1 = _compute_hash("LWC-001", 0, "2026-08-05T10:00:00Z")
    h2 = _compute_hash("LWC-001", 0, "2026-08-05T10:00:00Z")
    assert h1 == h2


def test_compute_hash_differs_on_index_change() -> None:
    h1 = _compute_hash("LWC-001", 0, "2026-08-05T10:00:00Z")
    h2 = _compute_hash("LWC-001", 1, "2026-08-05T10:00:00Z")
    assert h1 != h2


def test_compute_hash_differs_on_charter_change() -> None:
    h1 = _compute_hash("LWC-001", 0, "ts")
    h2 = _compute_hash("LWC-002", 0, "ts")
    assert h1 != h2


def test_compute_hash_length_is_64() -> None:
    assert len(_compute_hash("LWC-001", 0, "ts")) == 64


# ── _map_decision_type ────────────────────────────────────────────────────────


def test_map_decision_type_learning_oriented_is_strategic() -> None:
    assert _map_decision_type("Learning-Oriented") == "Strategic"


def test_map_decision_type_corrective_is_operational() -> None:
    assert _map_decision_type("Corrective") == "Operational"


def test_map_decision_type_preventive_is_operational() -> None:
    assert _map_decision_type("Preventive") == "Operational"


def test_map_decision_type_optimizing_is_operational() -> None:
    assert _map_decision_type("Optimizing") == "Operational"


# ── _map_criticality ──────────────────────────────────────────────────────────


def test_map_criticality_passes_through_valid_bands() -> None:
    for band in ("High", "Medium", "Low"):
        assert _map_criticality(band) == band


def test_map_criticality_unknown_defaults_to_medium() -> None:
    assert _map_criticality("Unknown") == "Medium"


# ── accept() — happy path ─────────────────────────────────────────────────────


def test_accept_returns_decision_record_and_trace_names() -> None:
    data = _make_recommendation_data()
    svc = RecommendationService()
    with _mock_service() as (mock_f, dr_doc, trace_doc, _):
        result = svc.accept("LWC-001", data)
    assert result["decision_record"] == "DR-2026-00042"
    assert result["trace_record"] == "ADRT-2026-00001"


def test_accept_inserts_decision_record_and_trace() -> None:
    data = _make_recommendation_data()
    svc = RecommendationService()
    with _mock_service() as (mock_f, dr_doc, trace_doc, _):
        svc.accept("LWC-001", data)
    dr_doc.insert.assert_called_once_with(ignore_permissions=False)
    trace_doc.insert.assert_called_once_with(ignore_permissions=True)


def test_accept_commits_transaction() -> None:
    data = _make_recommendation_data()
    svc = RecommendationService()
    with _mock_service() as (mock_f, _, _, _):
        svc.accept("LWC-001", data)
    mock_f.db.commit.assert_called_once()


def test_accept_decision_record_has_correct_charter_link() -> None:
    data = _make_recommendation_data()
    svc = RecommendationService()
    with _mock_service() as (_, dr_doc, _, _):
        svc.accept("LWC-2026-00001", data)
    assert dr_doc.lighthouse_workflow_charter == "LWC-2026-00001"


def test_accept_decision_record_owner_is_session_user() -> None:
    data = _make_recommendation_data()
    svc = RecommendationService()
    with _mock_service() as (_, dr_doc, _, _):
        svc.accept("LWC-001", data)
    assert dr_doc.accountable_owner == "alice@example.com"


def test_accept_trace_receives_hash() -> None:
    data = _make_recommendation_data()
    svc = RecommendationService()
    expected_hash = _compute_hash(
        "LWC-001", data["index"], data["execution_timestamp"]
    )
    with _mock_service() as (_, _, trace_doc, _):
        svc.accept("LWC-001", data)
    assert trace_doc.source_recommendation_hash == expected_hash


def test_accept_trace_linked_to_decision_record() -> None:
    data = _make_recommendation_data()
    svc = RecommendationService()
    with _mock_service() as (_, _, trace_doc, _):
        svc.accept("LWC-001", data)
    assert trace_doc.decision_record == "DR-2026-00042"


def test_accept_decision_record_assumptions_populated() -> None:
    data = _make_recommendation_data()
    svc = RecommendationService()
    with _mock_service() as (_, dr_doc, _, _):
        svc.accept("LWC-001", data)
    assert len(dr_doc.assumptions) >= 1
    assert all("assumption_text" in row for row in dr_doc.assumptions)


def test_accept_context_snapshot_in_trace() -> None:
    data = _make_recommendation_data()
    svc = RecommendationService()
    with _mock_service() as (_, _, trace_doc, _):
        svc.accept("LWC-001", data)
    assert trace_doc.context_snapshot  # non-empty JSON string


# ── accept() — idempotency ────────────────────────────────────────────────────


def test_accept_returns_existing_when_hash_already_present() -> None:
    data = _make_recommendation_data()
    existing = {"name": "ADRT-OLD", "decision_record": "DR-OLD"}
    svc = RecommendationService()
    with _mock_service(existing_trace=existing) as (mock_f, dr_doc, trace_doc, _):
        result = svc.accept("LWC-001", data)
    # Should not insert anything
    dr_doc.insert.assert_not_called()
    trace_doc.insert.assert_not_called()
    assert result["decision_record"] == "DR-OLD"
    assert result["trace_record"] == "ADRT-OLD"


def test_accept_race_condition_returns_existing_on_unique_error() -> None:
    data = _make_recommendation_data()
    existing = {"name": "ADRT-RACE", "decision_record": "DR-RACE"}
    svc = RecommendationService()

    call_count = [0]

    def get_all_side_effect(doctype, filters=None, fields=None, limit=None):
        call_count[0] += 1
        if call_count[0] == 1:
            return []  # first check: not found
        return [existing]  # second check (after rollback): found

    with _mock_service(
        raise_on_trace_insert=_frappe_module.UniqueValidationError("duplicate")
    ) as (mock_f, dr_doc, trace_doc, _):
        mock_f.get_all.side_effect = get_all_side_effect
        result = svc.accept("LWC-001", data)

    mock_f.db.rollback.assert_called_once()
    assert result["decision_record"] == "DR-RACE"


# ── accept() — validation ─────────────────────────────────────────────────────


def test_accept_invalid_schema_raises_validation_error() -> None:
    svc = RecommendationService()
    with _mock_service() as (_, _, _, _):
        with pytest.raises(_frappe_module.ValidationError):
            svc.accept("LWC-001", {"garbage": True})


def test_accept_race_condition_reraises_when_trace_still_not_found() -> None:
    """If UniqueValidationError fires but the trace still isn't in DB, re-raise."""
    data = _make_recommendation_data()
    svc = RecommendationService()
    with _mock_service(
        raise_on_trace_insert=_frappe_module.UniqueValidationError("duplicate"),
    ) as (mock_f, _, _, _):
        # get_all always returns [] — no trace found even after rollback
        mock_f.get_all.return_value = []
        with pytest.raises(_frappe_module.UniqueValidationError):
            svc.accept("LWC-001", data)


def test_accept_rollback_on_general_exception() -> None:
    data = _make_recommendation_data()
    svc = RecommendationService()
    with _mock_service(raise_on_trace_insert=RuntimeError("unexpected")) as (mock_f, _, _, _):
        with pytest.raises(RuntimeError):
            svc.accept("LWC-001", data)
    mock_f.db.rollback.assert_called_once()


# ── reject() — happy path ─────────────────────────────────────────────────────


def test_reject_returns_rejection_log_name() -> None:
    data = _make_recommendation_data()
    svc = RecommendationService()
    with _mock_service() as (_, _, _, rej_doc):
        result = svc.reject("LWC-001", data, "Insufficient evidence")
    assert result["rejection_log"] == "ARRL-2026-00001"


def test_reject_inserts_rejection_log() -> None:
    data = _make_recommendation_data()
    svc = RecommendationService()
    with _mock_service() as (_, _, _, rej_doc):
        svc.reject("LWC-001", data, "Not actionable")
    rej_doc.insert.assert_called_once_with(ignore_permissions=False)


def test_reject_logs_reason() -> None:
    data = _make_recommendation_data()
    svc = RecommendationService()
    with _mock_service() as (_, _, _, rej_doc):
        svc.reject("LWC-001", data, "Not relevant")
    assert rej_doc.reason == "Not relevant"


def test_reject_logs_charter_name() -> None:
    data = _make_recommendation_data()
    svc = RecommendationService()
    with _mock_service() as (_, _, _, rej_doc):
        svc.reject("LWC-2026-00001", data, "Reason")
    assert rej_doc.charter == "LWC-2026-00001"


def test_reject_commits_transaction() -> None:
    data = _make_recommendation_data()
    svc = RecommendationService()
    with _mock_service() as (mock_f, _, _, _):
        svc.reject("LWC-001", data, "Reason")
    mock_f.db.commit.assert_called_once()


# ── reject() — validation ─────────────────────────────────────────────────────


def test_reject_empty_reason_raises_validation_error() -> None:
    data = _make_recommendation_data()
    svc = RecommendationService()
    with _mock_service() as (_, _, _, _):
        with pytest.raises(_frappe_module.ValidationError):
            svc.reject("LWC-001", data, "   ")


def test_reject_invalid_schema_raises_validation_error() -> None:
    svc = RecommendationService()
    with _mock_service() as (_, _, _, _):
        with pytest.raises(_frappe_module.ValidationError):
            svc.reject("LWC-001", {"bad": "data"}, "Reason")
