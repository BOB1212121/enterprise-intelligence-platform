"""Tests for api/recommendations.py.

All frappe calls, reader, agent and service are mocked.
No Frappe site context required.

Run with:  python -m pytest enterprise_intelligence_platform/tests/test_api_recommendations.py -v
"""
from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

import frappe as _frappe_module

from enterprise_intelligence_platform.ai_agent.engine.null_engine import NullEngine
from enterprise_intelligence_platform.ai_agent.agent import ReasoningAgent
from enterprise_intelligence_platform.ai_agent.schemas import (
    CanonicalDecisionSignal,
    CanonicalDependencySignal,
    CanonicalKPISignal,
    CanonicalActionSignal,
    CharterContext,
    recommendation_to_dict,
)
from enterprise_intelligence_platform.api.recommendations import (
    get_ai_recommendations,
    accept_recommendation,
    reject_recommendation,
)

_API = "enterprise_intelligence_platform.api.recommendations"

# ── Shared fixture data ───────────────────────────────────────────────────────


def _charter_context() -> CharterContext:
    return CharterContext(
        charter_name="LWC-2026-00001",
        business_objective="Reduce DRR below 8%",
        in_scope_definition="Q3 ops",
        open_decisions=(
            CanonicalDecisionSignal(
                name="DR-001", state="Draft", criticality="High",
                decision_type="Operational", owner="alice@example.com",
            ),
        ),
        open_dependencies=(),
        kpi_signals=(CanonicalKPISignal(kpi_code="DRR", baseline_value=12.0, data_source="ERP"),),
        overdue_actions=(),
    )


def _valid_recommendation_data() -> dict[str, Any]:
    """Build a valid recommendation payload using a real pipeline."""
    ctx = _charter_context()
    pkg = ReasoningAgent(engine=NullEngine()).generate(ctx)
    rec = pkg.recommendations[0]
    data = recommendation_to_dict(rec)
    data.update({
        "model_identifier": pkg.model_identifier,
        "fallback_used": pkg.fallback_used,
        "execution_timestamp": pkg.execution_timestamp,
        "context_snapshot": pkg.context_snapshot,
    })
    return data


def _valid_rec_json() -> str:
    return json.dumps(_valid_recommendation_data())


# ── Shared mock context manager ───────────────────────────────────────────────


@contextmanager
def _mock_api(
    has_permission: bool = True,
    permission_error_on: str | None = None,
    approval_state: str | None = "Baseline Accepted",
    reader_context: CharterContext | None = None,
    agent_package: MagicMock | None = None,
    accept_result: dict | None = None,
    reject_result: dict | None = None,
    reader_raises: Exception | None = None,
    agent_raises: Exception | None = None,
    service_raises: Exception | None = None,
):
    with patch(f"{_API}.frappe") as mock_f, \
         patch(f"{_API}.ERPNextContextReader") as mock_reader_cls, \
         patch(f"{_API}.ReasoningAgent") as mock_agent_cls, \
         patch(f"{_API}.RecommendationService") as mock_svc_cls:

        # Frappe exceptions
        mock_f.DoesNotExistError = _frappe_module.DoesNotExistError
        mock_f.ValidationError = _frappe_module.ValidationError
        mock_f.PermissionError = _frappe_module.PermissionError

        # frappe.throw always raises
        def _throw(msg: str, exc=None, *args, **kwargs) -> None:
            raise (exc or Exception)(msg)
        mock_f.throw.side_effect = _throw

        # Permission check
        if not has_permission:
            mock_f.has_permission.side_effect = _frappe_module.PermissionError("Access denied")
        elif permission_error_on:
            def selective_perm(doctype, ptype="read", *a, throw=False, **kw):
                if doctype == permission_error_on:
                    raise _frappe_module.PermissionError("Access denied")
            mock_f.has_permission.side_effect = selective_perm

        # Charter state lookup
        mock_f.db.get_value.return_value = approval_state

        # Reader
        ctx = reader_context if reader_context is not None else _charter_context()
        if reader_raises:
            mock_reader_cls.return_value.read.side_effect = reader_raises
        else:
            mock_reader_cls.return_value.read.return_value = ctx

        # Agent
        pkg = agent_package
        if pkg is None:
            pkg = MagicMock()
            pkg.to_api_dict.return_value = {
                "charter_name": "LWC-2026-00001",
                "recommendations": [],
                "model_identifier": "null:deterministic",
                "fallback_used": True,
                "execution_timestamp": "2026-08-05T10:00:00Z",
                "context_snapshot": {},
            }
        if agent_raises:
            mock_agent_cls.return_value.generate.side_effect = agent_raises
        else:
            mock_agent_cls.return_value.generate.return_value = pkg

        # Service
        if service_raises:
            mock_svc_cls.return_value.accept.side_effect = service_raises
            mock_svc_cls.return_value.reject.side_effect = service_raises
        else:
            mock_svc_cls.return_value.accept.return_value = (
                accept_result or {"decision_record": "DR-042", "trace_record": "ADRT-001"}
            )
            mock_svc_cls.return_value.reject.return_value = (
                reject_result or {"rejection_log": "ARRL-001"}
            )

        yield mock_f, mock_reader_cls, mock_agent_cls, mock_svc_cls


# ── get_ai_recommendations ────────────────────────────────────────────────────


def test_get_ai_recommendations_success_returns_package_dict() -> None:
    with _mock_api() as (mock_f, _, _, _):
        result = get_ai_recommendations("LWC-001")
    assert result["charter_name"] == "LWC-2026-00001"
    assert "recommendations" in result


def test_get_ai_recommendations_calls_has_permission() -> None:
    with _mock_api() as (mock_f, _, _, _):
        get_ai_recommendations("LWC-001")
    mock_f.has_permission.assert_called_once()


def test_get_ai_recommendations_permission_denied_raises() -> None:
    with _mock_api(has_permission=False) as _:
        with pytest.raises(_frappe_module.PermissionError):
            get_ai_recommendations("LWC-001")


def test_get_ai_recommendations_missing_charter_raises() -> None:
    with _mock_api(approval_state=None) as _:
        with pytest.raises(_frappe_module.DoesNotExistError):
            get_ai_recommendations("LWC-MISSING")


def test_get_ai_recommendations_wrong_state_raises() -> None:
    with _mock_api(approval_state="Draft") as _:
        with pytest.raises(_frappe_module.ValidationError):
            get_ai_recommendations("LWC-001")


def test_get_ai_recommendations_reader_exception_propagates() -> None:
    with _mock_api(reader_raises=RuntimeError("DB error")) as _:
        with pytest.raises(RuntimeError, match="DB error"):
            get_ai_recommendations("LWC-001")


def test_get_ai_recommendations_agent_exception_propagates() -> None:
    with _mock_api(agent_raises=ValueError("bad context")) as _:
        with pytest.raises(ValueError, match="bad context"):
            get_ai_recommendations("LWC-001")


def test_get_ai_recommendations_creates_reader_and_agent() -> None:
    with _mock_api() as (_, mock_reader_cls, mock_agent_cls, _):
        get_ai_recommendations("LWC-001")
    mock_reader_cls.assert_called_once()
    mock_agent_cls.assert_called_once()


def test_get_ai_recommendations_reader_receives_charter_name() -> None:
    with _mock_api() as (_, mock_reader_cls, _, _):
        get_ai_recommendations("LWC-TEST")
    mock_reader_cls.return_value.read.assert_called_once_with("LWC-TEST")


def test_get_ai_recommendations_returns_to_api_dict_output() -> None:
    expected = {"charter_name": "X", "recommendations": [], "model_identifier": "y",
                "fallback_used": False, "execution_timestamp": "ts", "context_snapshot": {}}
    pkg = MagicMock()
    pkg.to_api_dict.return_value = expected
    with _mock_api(agent_package=pkg) as _:
        result = get_ai_recommendations("LWC-001")
    assert result == expected


# ── accept_recommendation ─────────────────────────────────────────────────────


def test_accept_recommendation_success_returns_service_result() -> None:
    with _mock_api() as _:
        result = accept_recommendation("LWC-001", _valid_rec_json())
    assert result["decision_record"] == "DR-042"
    assert result["trace_record"] == "ADRT-001"


def test_accept_recommendation_calls_has_permission() -> None:
    with _mock_api() as (mock_f, _, _, _):
        accept_recommendation("LWC-001", _valid_rec_json())
    mock_f.has_permission.assert_called_once_with("Decision Record", "create", throw=True)


def test_accept_recommendation_permission_denied_raises() -> None:
    with _mock_api(has_permission=False) as _:
        with pytest.raises(_frappe_module.PermissionError):
            accept_recommendation("LWC-001", _valid_rec_json())


def test_accept_recommendation_malformed_json_raises() -> None:
    with _mock_api() as _:
        with pytest.raises(_frappe_module.ValidationError):
            accept_recommendation("LWC-001", "{not valid json}")


def test_accept_recommendation_invalid_schema_raises() -> None:
    with _mock_api() as _:
        with pytest.raises(_frappe_module.ValidationError):
            accept_recommendation("LWC-001", json.dumps({"garbage": True}))


def test_accept_recommendation_delegates_to_service() -> None:
    data = _valid_recommendation_data()
    with _mock_api() as (_, _, _, mock_svc_cls):
        accept_recommendation("LWC-001", json.dumps(data))
    mock_svc_cls.return_value.accept.assert_called_once_with("LWC-001", data)


def test_accept_recommendation_service_exception_propagates() -> None:
    with _mock_api(service_raises=RuntimeError("DB down")) as _:
        with pytest.raises(RuntimeError, match="DB down"):
            accept_recommendation("LWC-001", _valid_rec_json())


# ── reject_recommendation ─────────────────────────────────────────────────────


def test_reject_recommendation_success_returns_service_result() -> None:
    with _mock_api() as _:
        result = reject_recommendation("LWC-001", _valid_rec_json(), "Not actionable")
    assert result["rejection_log"] == "ARRL-001"


def test_reject_recommendation_calls_has_permission() -> None:
    with _mock_api() as (mock_f, _, _, _):
        reject_recommendation("LWC-001", _valid_rec_json(), "reason")
    mock_f.has_permission.assert_called_once()


def test_reject_recommendation_permission_denied_raises() -> None:
    with _mock_api(has_permission=False) as _:
        with pytest.raises(_frappe_module.PermissionError):
            reject_recommendation("LWC-001", _valid_rec_json(), "reason")


def test_reject_recommendation_malformed_json_raises() -> None:
    with _mock_api() as _:
        with pytest.raises(_frappe_module.ValidationError):
            reject_recommendation("LWC-001", "bad json", "reason")


def test_reject_recommendation_invalid_schema_raises() -> None:
    with _mock_api() as _:
        with pytest.raises(_frappe_module.ValidationError):
            reject_recommendation("LWC-001", json.dumps({"bad": "schema"}), "reason")


def test_reject_recommendation_empty_reason_raises() -> None:
    with _mock_api() as _:
        with pytest.raises(_frappe_module.ValidationError):
            reject_recommendation("LWC-001", _valid_rec_json(), "   ")


def test_reject_recommendation_delegates_to_service() -> None:
    data = _valid_recommendation_data()
    with _mock_api() as (_, _, _, mock_svc_cls):
        reject_recommendation("LWC-001", json.dumps(data), "No evidence")
    mock_svc_cls.return_value.reject.assert_called_once_with("LWC-001", data, "No evidence")


def test_reject_recommendation_service_exception_propagates() -> None:
    with _mock_api(service_raises=RuntimeError("DB down")) as _:
        with pytest.raises(RuntimeError, match="DB down"):
            reject_recommendation("LWC-001", _valid_rec_json(), "reason")
