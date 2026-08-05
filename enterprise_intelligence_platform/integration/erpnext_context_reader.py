"""ERPNextContextReader — Anti-Corruption Layer (Phase 19 Extension Point E3).

This is the ONLY module permitted to reference ERPNext DocType names or field names.
Every value that crosses this boundary is translated into a canonical AI domain object.
No ERPNext terminology may escape to the ReasoningAgent or any reasoning layer.

Governance authority:
  INTEGRATION_ARCHITECTURE.md §2 (ERP-agnostic contract model)
  INTEGRATION_ARCHITECTURE.md §3 (anti-corruption and semantic translation)
  REFERENCE_ARCHITECTURE.md §8  (extension point E3)
"""
from __future__ import annotations

from datetime import date

import frappe
from frappe.utils import today as frappe_today

from enterprise_intelligence_platform.ai_agent.schemas import (
    CanonicalActionSignal,
    CanonicalDecisionSignal,
    CanonicalDependencySignal,
    CanonicalKPISignal,
    CharterContext,
)

# ── DocType names — ACL boundary; must not escape this file ───────────────────

_DT_CHARTER = "Lighthouse Workflow Charter"
_DT_DECISION = "Decision Record"
_DT_DEPENDENCY = "Dependency Exception Record"
_DT_TASK = "Task"

_CLOSED_DECISION_STATES = frozenset({"Approved", "Rejected"})
_CLOSED_DEPENDENCY_STATUSES = frozenset({"Resolved"})
_CLOSED_TASK_STATUSES = frozenset({"Completed", "Cancelled"})


# ── Private helper ─────────────────────────────────────────────────────────────


def _days_overdue(target_date_str: str | None, today_str: str) -> int:
    """Return non-negative calendar days between target date and today.

    Returns 0 when target_date_str is None, unparseable, or not yet reached.
    """
    if not target_date_str:
        return 0
    try:
        target = date.fromisoformat(str(target_date_str))
        today_d = date.fromisoformat(str(today_str))
        return max(0, (today_d - target).days)
    except (ValueError, TypeError):
        return 0


# ── Reader ─────────────────────────────────────────────────────────────────────


class ERPNextContextReader:
    """Read ERPNext DocTypes and translate them into a canonical CharterContext.

    Only reads data — never writes.  Tolerates optional ERP modules by returning
    empty signal collections rather than raising.  Only the charter's absence
    propagates as an exception (frappe.DoesNotExistError).
    """

    def read(self, charter_name: str) -> CharterContext:
        """Load and translate a charter.

        Raises frappe.DoesNotExistError if the charter does not exist.
        All signal collections degrade gracefully to () on any other failure.
        """
        doc = self._fetch_charter(charter_name)
        return CharterContext(
            charter_name=charter_name,
            business_objective=str(doc.business_objective or "").strip(),
            in_scope_definition=str(doc.in_scope_definition or "").strip(),
            open_decisions=self._read_open_decisions(charter_name),
            open_dependencies=self._read_open_dependencies(charter_name),
            kpi_signals=self._read_kpi_signals(doc),
            overdue_actions=self._read_overdue_actions(doc),
        )

    # ── private read methods ──────────────────────────────────────────────────

    def _fetch_charter(self, charter_name: str):
        """Fetch the charter document; propagates DoesNotExistError."""
        return frappe.get_doc(_DT_CHARTER, charter_name)

    def _read_open_decisions(self, charter_name: str) -> tuple[CanonicalDecisionSignal, ...]:
        """Return non-closed Decision Records for this charter."""
        try:
            rows = frappe.get_all(
                _DT_DECISION,
                filters={
                    "lighthouse_workflow_charter": charter_name,
                    "approval_state": ["not in", list(_CLOSED_DECISION_STATES)],
                },
                fields=["name", "approval_state", "decision_criticality",
                        "decision_type", "accountable_owner"],
            )
            return tuple(
                CanonicalDecisionSignal(
                    name=str(row.name),
                    state=str(row.approval_state or "Draft"),
                    criticality=str(row.decision_criticality or "Medium"),
                    decision_type=str(row.decision_type or "Operational"),
                    owner=str(row.accountable_owner or ""),
                )
                for row in rows
            )
        except Exception:
            return ()

    def _read_open_dependencies(self, charter_name: str) -> tuple[CanonicalDependencySignal, ...]:
        """Return unresolved Dependency Exception Records for this charter."""
        today = frappe_today()
        try:
            rows = frappe.get_all(
                _DT_DEPENDENCY,
                filters={
                    "lighthouse_workflow_charter": charter_name,
                    "dependency_status": ["not in", list(_CLOSED_DEPENDENCY_STATUSES)],
                },
                fields=["name", "dependency_criticality", "dependency_status",
                        "dependency_type", "target_resolution_date"],
            )
            return tuple(
                CanonicalDependencySignal(
                    name=str(row.name),
                    criticality=str(row.dependency_criticality or "Medium"),
                    status=str(row.dependency_status or "Open"),
                    dependency_type=str(row.dependency_type or "System"),
                    days_overdue=_days_overdue(row.target_resolution_date, today),
                )
                for row in rows
            )
        except Exception:
            return ()

    def _read_kpi_signals(self, charter_doc) -> tuple[CanonicalKPISignal, ...]:
        """Translate the charter's baseline_kpis child table into canonical signals."""
        signals: list[CanonicalKPISignal] = []
        try:
            for row in (charter_doc.baseline_kpis or []):
                kpi_code = str(getattr(row, "kpi_code", "") or "").strip()
                if not kpi_code:
                    continue
                signals.append(CanonicalKPISignal(
                    kpi_code=kpi_code,
                    baseline_value=float(getattr(row, "baseline_value", 0) or 0),
                    data_source=str(getattr(row, "data_source", "") or ""),
                ))
        except Exception:
            pass
        return tuple(signals)

    def _read_overdue_actions(self, charter_doc) -> tuple[CanonicalActionSignal, ...]:
        """Proxy overdue commitments from ERPNext Tasks linked by project name prefix.

        Returns () when Task DocType is absent or no matching tasks exist.
        NOTE: A direct Charter → Project link is not yet in the schema.
        This implementation matches projects whose name starts with workflow_name.
        """
        workflow_name = str(getattr(charter_doc, "workflow_name", "") or "").strip()
        if not workflow_name:
            return ()
        today = frappe_today()
        try:
            rows = frappe.get_all(
                _DT_TASK,
                filters=[
                    ["project", "like", f"{workflow_name}%"],
                    ["exp_end_date", "<", today],
                    ["status", "not in", list(_CLOSED_TASK_STATUSES)],
                ],
                fields=["name", "exp_end_date", "assigned_to"],
            )
            return tuple(
                CanonicalActionSignal(
                    name=str(row.name),
                    overdue_days=_days_overdue(row.exp_end_date, today),
                    owner=str(row.assigned_to or ""),
                )
                for row in rows
            )
        except Exception:
            return ()


__all__ = ["ERPNextContextReader"]
