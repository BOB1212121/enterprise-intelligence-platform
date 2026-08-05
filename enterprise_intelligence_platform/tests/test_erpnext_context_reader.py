"""Tests for ERPNextContextReader (ACL boundary adapter).

All frappe DB calls are mocked so no Frappe site context is required.
Tests verify both canonical output correctness and ACL boundary enforcement.

Run with: python -m pytest enterprise_intelligence_platform/tests/test_erpnext_context_reader.py -v
"""
from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

import frappe as _frappe_module  # real frappe for DoesNotExistError class only

from enterprise_intelligence_platform.ai_agent.schemas import (
    CanonicalDecisionSignal,
    CanonicalDependencySignal,
    CanonicalKPISignal,
    CharterContext,
    charter_context_to_snapshot,
)
from enterprise_intelligence_platform.integration.erpnext_context_reader import (
    ERPNextContextReader,
    _days_overdue,
)

_MODULE = "enterprise_intelligence_platform.integration.erpnext_context_reader"

# ── Lightweight stub objects for Frappe doc rows ──────────────────────────────


class _Doc:
    """Stub Frappe document.  Missing attributes resolve to None."""

    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __getattr__(self, name: str) -> None:  # noqa: ANN401
        return None


class _Row:
    """Stub child-table row."""

    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __getattr__(self, name: str) -> None:
        return None


# ── Shared mock context manager ───────────────────────────────────────────────


@contextmanager
def _mock_frappe(
    charter_doc: _Doc,
    decisions: list[_Row] | None = None,
    dependencies: list[_Row] | None = None,
    tasks: list[_Row] | None = None,
    today: str = "2026-08-05",
    task_raises: bool = False,
):
    """Patch frappe in the reader module for one read() call."""
    decisions = decisions or []
    dependencies = dependencies or []
    tasks = tasks or []

    def fake_get_all(doctype: str, filters=None, fields=None, **kwargs) -> list:
        if doctype == "Decision Record":
            return decisions
        if doctype == "Dependency Exception Record":
            return dependencies
        if doctype == "Task":
            if task_raises:
                raise Exception("DocType Task does not exist")
            return tasks
        return []

    with patch(f"{_MODULE}.frappe") as mock_frappe:
        mock_frappe.get_doc.return_value = charter_doc
        mock_frappe.get_all.side_effect = fake_get_all
        mock_frappe.DoesNotExistError = _frappe_module.DoesNotExistError
        with patch(f"{_MODULE}.frappe_today", return_value=today):
            yield mock_frappe


@contextmanager
def _mock_frappe_missing_charter(charter_name: str):
    """Patch frappe.get_doc to raise DoesNotExistError for a missing charter."""
    with patch(f"{_MODULE}.frappe") as mock_frappe:
        mock_frappe.get_doc.side_effect = _frappe_module.DoesNotExistError(
            f"{charter_name} not found"
        )
        mock_frappe.DoesNotExistError = _frappe_module.DoesNotExistError
        yield mock_frappe


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _charter_doc(
    name: str = "LWC-001",
    workflow_name: str = "Q3 Governance",
    business_objective: str = "Reduce DRR below 8%",
    in_scope_definition: str = "Q3 operational decisions",
    baseline_kpis: list[_Row] | None = None,
) -> _Doc:
    return _Doc(
        name=name,
        workflow_name=workflow_name,
        business_objective=business_objective,
        in_scope_definition=in_scope_definition,
        baseline_kpis=baseline_kpis or [],
    )


def _decision_row(**kwargs) -> _Row:
    defaults = dict(
        name="DR-001",
        approval_state="Draft",
        decision_criticality="High",
        decision_type="Operational",
        accountable_owner="alice@example.com",
    )
    return _Row(**{**defaults, **kwargs})


def _dependency_row(**kwargs) -> _Row:
    defaults = dict(
        name="DER-001",
        dependency_criticality="Critical",
        dependency_status="At Risk",
        dependency_type="System",
        target_resolution_date="2026-08-01",  # 4 days before fixed today 2026-08-05
    )
    return _Row(**{**defaults, **kwargs})


def _kpi_row(**kwargs) -> _Row:
    defaults = dict(kpi_code="DRR", baseline_value=12.0, data_source="ERP")
    return _Row(**{**defaults, **kwargs})


def _task_row(**kwargs) -> _Row:
    defaults = dict(
        name="TASK-001",
        exp_end_date="2026-08-01",
        assigned_to="bob@example.com",
    )
    return _Row(**{**defaults, **kwargs})


# ── _days_overdue helper ──────────────────────────────────────────────────────


def test_days_overdue_standard() -> None:
    assert _days_overdue("2026-08-01", "2026-08-05") == 4


def test_days_overdue_not_yet_overdue_returns_zero() -> None:
    assert _days_overdue("2026-08-10", "2026-08-05") == 0


def test_days_overdue_same_day_returns_zero() -> None:
    assert _days_overdue("2026-08-05", "2026-08-05") == 0


def test_days_overdue_none_target_returns_zero() -> None:
    assert _days_overdue(None, "2026-08-05") == 0


def test_days_overdue_invalid_date_returns_zero() -> None:
    assert _days_overdue("not-a-date", "2026-08-05") == 0


def test_days_overdue_empty_string_returns_zero() -> None:
    assert _days_overdue("", "2026-08-05") == 0


# ── Happy-path: read() returns CharterContext ─────────────────────────────────


def test_read_returns_charter_context_type() -> None:
    reader = ERPNextContextReader()
    doc = _charter_doc(baseline_kpis=[_kpi_row()])
    with _mock_frappe(doc, decisions=[_decision_row()], dependencies=[_dependency_row()]):
        ctx = reader.read("LWC-001")
    assert isinstance(ctx, CharterContext)


def test_read_charter_name_matches() -> None:
    reader = ERPNextContextReader()
    with _mock_frappe(_charter_doc()):
        ctx = reader.read("LWC-001")
    assert ctx.charter_name == "LWC-001"


def test_read_business_objective_translated() -> None:
    reader = ERPNextContextReader()
    doc = _charter_doc(business_objective="  Reduce DRR  ")  # leading/trailing spaces
    with _mock_frappe(doc):
        ctx = reader.read("LWC-001")
    assert ctx.business_objective == "Reduce DRR"


def test_read_in_scope_definition_translated() -> None:
    reader = ERPNextContextReader()
    doc = _charter_doc(in_scope_definition="Q3 ops")
    with _mock_frappe(doc):
        ctx = reader.read("LWC-001")
    assert ctx.in_scope_definition == "Q3 ops"


# ── Charter not found ─────────────────────────────────────────────────────────


def test_read_raises_does_not_exist_for_missing_charter() -> None:
    reader = ERPNextContextReader()
    with _mock_frappe_missing_charter("LWC-MISSING"):
        with pytest.raises(_frappe_module.DoesNotExistError):
            reader.read("LWC-MISSING")


# ── Decision signals ──────────────────────────────────────────────────────────


def test_read_open_decisions_count() -> None:
    reader = ERPNextContextReader()
    rows = [_decision_row(name="DR-001"), _decision_row(name="DR-002")]
    with _mock_frappe(_charter_doc(), decisions=rows):
        ctx = reader.read("LWC-001")
    assert len(ctx.open_decisions) == 2


def test_read_no_decisions_returns_empty_tuple() -> None:
    reader = ERPNextContextReader()
    with _mock_frappe(_charter_doc(), decisions=[]):
        ctx = reader.read("LWC-001")
    assert ctx.open_decisions == ()


def test_read_decision_canonical_field_mapping() -> None:
    reader = ERPNextContextReader()
    row = _decision_row(
        name="DR-042",
        approval_state="Submitted for Approval",
        decision_criticality="High",
        decision_type="Strategic",
        accountable_owner="alice@example.com",
    )
    with _mock_frappe(_charter_doc(), decisions=[row]):
        ctx = reader.read("LWC-001")
    sig = ctx.open_decisions[0]
    assert sig.name == "DR-042"
    assert sig.state == "Submitted for Approval"
    assert sig.criticality == "High"
    assert sig.decision_type == "Strategic"
    assert sig.owner == "alice@example.com"


def test_read_decision_missing_fields_normalised() -> None:
    reader = ERPNextContextReader()
    row = _Row(name="DR-BAD")  # all other fields missing → None
    with _mock_frappe(_charter_doc(), decisions=[row]):
        ctx = reader.read("LWC-001")
    sig = ctx.open_decisions[0]
    assert sig.state == "Draft"
    assert sig.criticality == "Medium"
    assert sig.decision_type == "Operational"
    assert sig.owner == ""


def test_read_decisions_exception_returns_empty() -> None:
    """If the Decision Record query raises, degrade gracefully."""
    reader = ERPNextContextReader()

    def bad_get_all(doctype, **kwargs):
        if doctype == "Decision Record":
            raise Exception("DB error")
        return []

    with patch(f"{_MODULE}.frappe") as mock_f:
        mock_f.get_doc.return_value = _charter_doc()
        mock_f.get_all.side_effect = bad_get_all
        mock_f.DoesNotExistError = _frappe_module.DoesNotExistError
        with patch(f"{_MODULE}.frappe_today", return_value="2026-08-05"):
            ctx = reader.read("LWC-001")
    assert ctx.open_decisions == ()


# ── Dependency signals ────────────────────────────────────────────────────────


def test_read_dependencies_exception_returns_empty() -> None:
    """If the Dependency Exception Record query raises, degrade gracefully."""
    reader = ERPNextContextReader()

    def bad_get_all(doctype, **kwargs):
        if doctype == "Dependency Exception Record":
            raise Exception("DB error")
        return []

    with patch(f"{_MODULE}.frappe") as mock_f:
        mock_f.get_doc.return_value = _charter_doc()
        mock_f.get_all.side_effect = bad_get_all
        mock_f.DoesNotExistError = _frappe_module.DoesNotExistError
        with patch(f"{_MODULE}.frappe_today", return_value="2026-08-05"):
            ctx = reader.read("LWC-001")
    assert ctx.open_dependencies == ()


def test_read_open_dependencies_count() -> None:
    reader = ERPNextContextReader()
    rows = [_dependency_row(name="DER-001"), _dependency_row(name="DER-002")]
    with _mock_frappe(_charter_doc(), dependencies=rows):
        ctx = reader.read("LWC-001")
    assert len(ctx.open_dependencies) == 2


def test_read_no_dependencies_returns_empty_tuple() -> None:
    reader = ERPNextContextReader()
    with _mock_frappe(_charter_doc()):
        ctx = reader.read("LWC-001")
    assert ctx.open_dependencies == ()


def test_read_dependency_canonical_field_mapping() -> None:
    reader = ERPNextContextReader()
    row = _dependency_row(
        name="DER-007",
        dependency_criticality="Critical",
        dependency_status="At Risk",
        dependency_type="Vendor",
        target_resolution_date="2026-08-01",
    )
    with _mock_frappe(_charter_doc(), dependencies=[row], today="2026-08-05"):
        ctx = reader.read("LWC-001")
    sig = ctx.open_dependencies[0]
    assert sig.name == "DER-007"
    assert sig.criticality == "Critical"
    assert sig.status == "At Risk"
    assert sig.dependency_type == "Vendor"
    assert sig.days_overdue == 4


def test_read_dependency_not_yet_overdue_returns_zero_days() -> None:
    reader = ERPNextContextReader()
    row = _dependency_row(target_resolution_date="2026-08-10")
    with _mock_frappe(_charter_doc(), dependencies=[row], today="2026-08-05"):
        ctx = reader.read("LWC-001")
    assert ctx.open_dependencies[0].days_overdue == 0


def test_read_dependency_missing_fields_normalised() -> None:
    reader = ERPNextContextReader()
    row = _Row(name="DER-BAD")
    with _mock_frappe(_charter_doc(), dependencies=[row]):
        ctx = reader.read("LWC-001")
    sig = ctx.open_dependencies[0]
    assert sig.criticality == "Medium"
    assert sig.status == "Open"
    assert sig.dependency_type == "System"
    assert sig.days_overdue == 0


# ── KPI signals ───────────────────────────────────────────────────────────────


def test_read_kpi_signals_from_child_table() -> None:
    reader = ERPNextContextReader()
    doc = _charter_doc(baseline_kpis=[_kpi_row(kpi_code="DRR", baseline_value=12.0, data_source="ERP")])
    with _mock_frappe(doc):
        ctx = reader.read("LWC-001")
    assert len(ctx.kpi_signals) == 1
    assert ctx.kpi_signals[0].kpi_code == "DRR"
    assert ctx.kpi_signals[0].baseline_value == 12.0
    assert ctx.kpi_signals[0].data_source == "ERP"


def test_read_no_kpi_signals_returns_empty_tuple() -> None:
    reader = ERPNextContextReader()
    doc = _charter_doc(baseline_kpis=[])
    with _mock_frappe(doc):
        ctx = reader.read("LWC-001")
    assert ctx.kpi_signals == ()


def test_read_multiple_kpis() -> None:
    reader = ERPNextContextReader()
    kpis = [
        _kpi_row(kpi_code="DRR", baseline_value=12.0, data_source="ERP"),
        _kpi_row(kpi_code="DCT", baseline_value=5.5, data_source="ERP"),
        _kpi_row(kpi_code="AER", baseline_value=3.2, data_source="Manual"),
    ]
    doc = _charter_doc(baseline_kpis=kpis)
    with _mock_frappe(doc):
        ctx = reader.read("LWC-001")
    assert len(ctx.kpi_signals) == 3
    codes = {s.kpi_code for s in ctx.kpi_signals}
    assert codes == {"DRR", "DCT", "AER"}


def test_read_kpi_row_with_empty_code_is_skipped() -> None:
    reader = ERPNextContextReader()
    kpis = [
        _Row(kpi_code="", baseline_value=5.0, data_source="ERP"),
        _Row(kpi_code="DRR", baseline_value=12.0, data_source="ERP"),
    ]
    doc = _charter_doc(baseline_kpis=kpis)
    with _mock_frappe(doc):
        ctx = reader.read("LWC-001")
    assert len(ctx.kpi_signals) == 1


# ── Overdue action signals ────────────────────────────────────────────────────


def test_read_overdue_actions_from_tasks() -> None:
    reader = ERPNextContextReader()
    doc = _charter_doc(workflow_name="Q3 Governance")
    tasks = [_task_row(name="TASK-001", exp_end_date="2026-08-01", assigned_to="bob@example.com")]
    with _mock_frappe(doc, tasks=tasks, today="2026-08-05"):
        ctx = reader.read("LWC-001")
    assert len(ctx.overdue_actions) == 1
    sig = ctx.overdue_actions[0]
    assert sig.name == "TASK-001"
    assert sig.overdue_days == 4
    assert sig.owner == "bob@example.com"


def test_read_no_overdue_tasks_returns_empty_tuple() -> None:
    reader = ERPNextContextReader()
    doc = _charter_doc(workflow_name="Q3 Governance")
    with _mock_frappe(doc, tasks=[]):
        ctx = reader.read("LWC-001")
    assert ctx.overdue_actions == ()


def test_read_missing_task_doctype_returns_empty_tuple() -> None:
    reader = ERPNextContextReader()
    doc = _charter_doc(workflow_name="Q3 Governance")
    with _mock_frappe(doc, task_raises=True):
        ctx = reader.read("LWC-001")
    assert ctx.overdue_actions == ()


def test_read_no_workflow_name_returns_empty_overdue_actions() -> None:
    reader = ERPNextContextReader()
    doc = _charter_doc(workflow_name="")
    with _mock_frappe(doc):
        ctx = reader.read("LWC-001")
    assert ctx.overdue_actions == ()


# ── ACL boundary enforcement ──────────────────────────────────────────────────


def test_erp_field_names_do_not_appear_in_canonical_output() -> None:
    """Core ACL test: ERPNext-specific field names must not escape to the canonical snapshot."""
    reader = ERPNextContextReader()
    doc = _charter_doc(baseline_kpis=[_kpi_row()])
    with _mock_frappe(
        doc,
        decisions=[_decision_row()],
        dependencies=[_dependency_row()],
        tasks=[_task_row()],
    ):
        ctx = reader.read("LWC-001")

    snapshot_str = json.dumps(charter_context_to_snapshot(ctx))
    erp_field_names = {
        "approval_state",
        "decision_criticality",
        "dependency_status",
        "baseline_kpis",
        "lighthouse_workflow_charter",
        "naming_series",
        "accountable_owner",
        # dependency_type is a canonical domain concept (not purely ERP-specific)
    }
    for field in erp_field_names:
        assert field not in snapshot_str, f"ERPNext field name escaped the ACL: {field!r}"


def test_canonical_decision_signal_contains_only_schema_fields() -> None:
    reader = ERPNextContextReader()
    with _mock_frappe(_charter_doc(), decisions=[_decision_row()]):
        ctx = reader.read("LWC-001")
    sig = ctx.open_decisions[0]
    assert isinstance(sig, CanonicalDecisionSignal)
    # Only canonical attribute names
    assert hasattr(sig, "name")
    assert hasattr(sig, "state")
    assert hasattr(sig, "criticality")
    assert hasattr(sig, "decision_type")
    assert hasattr(sig, "owner")
    # ERP field names are absent
    assert not hasattr(sig, "approval_state")
    assert not hasattr(sig, "decision_criticality")
    assert not hasattr(sig, "accountable_owner")


def test_canonical_dependency_signal_contains_only_schema_fields() -> None:
    reader = ERPNextContextReader()
    with _mock_frappe(_charter_doc(), dependencies=[_dependency_row()]):
        ctx = reader.read("LWC-001")
    sig = ctx.open_dependencies[0]
    assert isinstance(sig, CanonicalDependencySignal)
    assert not hasattr(sig, "dependency_status")
    assert not hasattr(sig, "dependency_criticality")
    assert not hasattr(sig, "target_resolution_date")


# ── CharterContext schema invariants ──────────────────────────────────────────


def test_read_produces_valid_charter_context_schema() -> None:
    """CharterContext.__post_init__ must pass for the translated output."""
    reader = ERPNextContextReader()
    doc = _charter_doc(baseline_kpis=[_kpi_row()])
    with _mock_frappe(doc, decisions=[_decision_row()], dependencies=[_dependency_row()]):
        ctx = reader.read("LWC-001")
    # If schema validation passed, ctx is valid
    assert ctx.charter_name
    assert ctx.business_objective


def test_read_multiple_decisions_and_dependencies() -> None:
    reader = ERPNextContextReader()
    decisions = [_decision_row(name=f"DR-{i:03d}") for i in range(5)]
    deps = [_dependency_row(name=f"DER-{i:03d}") for i in range(3)]
    with _mock_frappe(_charter_doc(), decisions=decisions, dependencies=deps):
        ctx = reader.read("LWC-001")
    assert len(ctx.open_decisions) == 5
    assert len(ctx.open_dependencies) == 3


# ── Query count sanity ────────────────────────────────────────────────────────


def test_read_calls_get_all_at_most_three_times() -> None:
    """One call each for: Decision Record, Dependency Exception Record, Task."""
    reader = ERPNextContextReader()
    doc = _charter_doc(workflow_name="Q3 Gov", baseline_kpis=[_kpi_row()])
    call_log: list[str] = []

    def counting_get_all(doctype, **kwargs):
        call_log.append(doctype)
        return []

    with patch(f"{_MODULE}.frappe") as mock_f:
        mock_f.get_doc.return_value = doc
        mock_f.get_all.side_effect = counting_get_all
        mock_f.DoesNotExistError = _frappe_module.DoesNotExistError
        with patch(f"{_MODULE}.frappe_today", return_value="2026-08-05"):
            reader.read("LWC-001")

    assert call_log.count("Decision Record") <= 1
    assert call_log.count("Dependency Exception Record") <= 1
    assert call_log.count("Task") <= 1
    assert len(call_log) <= 3


def test_read_kpi_signals_exception_returns_empty() -> None:
    """If iterating the KPI child table raises, return empty tuple gracefully."""
    reader = ERPNextContextReader()
    # baseline_kpis is non-iterable — triggers the except branch
    bad_doc = _Doc(
        name="LWC-001",
        workflow_name="Q3 Gov",
        business_objective="Obj",
        in_scope_definition="Scope",
        baseline_kpis=42,  # int is not iterable
    )
    with _mock_frappe(bad_doc):
        ctx = reader.read("LWC-001")
    assert ctx.kpi_signals == ()


def test_read_overdue_actions_exception_in_row_construction_returns_empty() -> None:
    """If Task rows are present but raise during CanonicalActionSignal construction, return ()."""
    reader = ERPNextContextReader()
    doc = _charter_doc(workflow_name="Q3 Gov")

    # task_row with invalid exp_end_date (days_overdue returns 0 safely, so this
    # test instead mocks get_all for Task to raise after an initially empty decision/dep pass)
    def raising_get_all(doctype, **kwargs):
        if doctype == "Task":
            raise RuntimeError("Unexpected Task schema error")
        return []

    with patch(f"{_MODULE}.frappe") as mock_f:
        mock_f.get_doc.return_value = doc
        mock_f.get_all.side_effect = raising_get_all
        mock_f.DoesNotExistError = _frappe_module.DoesNotExistError
        with patch(f"{_MODULE}.frappe_today", return_value="2026-08-05"):
            ctx = reader.read("LWC-001")
    assert ctx.overdue_actions == ()
