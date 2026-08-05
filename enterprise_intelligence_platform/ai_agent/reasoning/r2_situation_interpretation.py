"""R2 — Situation Interpretation.

Transforms an IntentFrame + CharterContext into a SituationAssessment
containing observations, risk indicators, and opportunity indicators.
R2 produces observations only — no decisions, no recommendations.

Fallback: derives assessments directly from CharterContext signal counts.
"""
from __future__ import annotations

from enterprise_intelligence_platform.ai_agent.engine.base import BaseInferenceEngine
from enterprise_intelligence_platform.ai_agent.reasoning.base import BaseReasoningLayer
from enterprise_intelligence_platform.ai_agent.schemas import (
    CharterContext,
    IntentFrame,
    SituationAssessment,
)


class R2SituationInterpretation(BaseReasoningLayer):
    """Interpret the current governance situation."""

    def execute(
        self,
        frame: IntentFrame,
        context: CharterContext,
        engine: BaseInferenceEngine,
    ) -> SituationAssessment:
        response = engine.complete(self._build_prompt(frame, context))
        if response.success:
            parsed = self._parse_llm_output(response.text)
            if parsed is not None:
                self.used_fallback = False
                return parsed
        self.used_fallback = True
        return self._fallback(frame, context)

    # ── prompt ───────────────────────────────────────────────────────────────

    def _build_prompt(self, frame: IntentFrame, context: CharterContext) -> str:
        kpi_text = (
            ", ".join(f"{k.kpi_code}={k.baseline_value}" for k in context.kpi_signals)
            or "none registered"
        )
        return (
            "Interpret the governance situation. Reply with ONLY valid JSON.\n\n"
            f"Objective: {frame.objective}\n"
            f"Open decisions: {len(context.open_decisions)}\n"
            f"Unresolved dependencies: {len(context.open_dependencies)}\n"
            f"Overdue commitments: {len(context.overdue_actions)}\n"
            f"KPI baselines: {kpi_text}\n\n"
            "Return JSON with keys:\n"
            '  "observations": list of factual observation strings,\n'
            '  "risk_indicators": list of risk signal strings,\n'
            '  "opportunity_indicators": list of opportunity strings,\n'
            '  "context_summary": one-sentence situation summary (string).'
        )

    # ── LLM output parsing ────────────────────────────────────────────────────

    def _parse_llm_output(self, text: str) -> SituationAssessment | None:
        data = self._try_parse_json(text)
        if not isinstance(data, dict):
            return None
        try:
            summary = str(data.get("context_summary") or "").strip()
            if not summary:
                return None
            return SituationAssessment(
                observations=tuple(str(o) for o in (data.get("observations") or []) if o),
                risk_indicators=tuple(str(r) for r in (data.get("risk_indicators") or []) if r),
                opportunity_indicators=tuple(
                    str(o) for o in (data.get("opportunity_indicators") or []) if o
                ),
                context_summary=summary,
            )
        except (TypeError, ValueError):
            return None

    # ── deterministic fallback ────────────────────────────────────────────────

    def _fallback(self, frame: IntentFrame, context: CharterContext) -> SituationAssessment:
        observations: list[str] = [f"Governance objective: {frame.objective}"]
        if context.open_decisions:
            observations.append(f"{len(context.open_decisions)} decision(s) are currently open")
        if context.open_dependencies:
            observations.append(
                f"{len(context.open_dependencies)} dependency exception(s) are unresolved"
            )
        if context.overdue_actions:
            observations.append(f"{len(context.overdue_actions)} commitment(s) are overdue")
        if context.kpi_signals:
            kpi_codes = ", ".join(k.kpi_code for k in context.kpi_signals)
            observations.append(f"Baseline KPIs registered: {kpi_codes}")

        risk_indicators: list[str] = []
        at_risk = [d for d in context.open_dependencies if d.status == "At Risk"]
        if at_risk:
            risk_indicators.append(f"{len(at_risk)} dependency exception(s) are currently at risk")
        critical_deps = [d for d in context.open_dependencies if d.criticality == "Critical"]
        if critical_deps:
            risk_indicators.append(
                f"{len(critical_deps)} critical dependency exception(s) may block execution"
            )
        if context.overdue_actions:
            max_overdue = max(a.overdue_days for a in context.overdue_actions)
            risk_indicators.append(f"Commitments are overdue by up to {max_overdue} days")

        opportunity_indicators: list[str] = []
        if context.kpi_signals:
            opportunity_indicators.append(
                "KPI baselines provide measurable targets for governance improvement"
            )
        if context.open_decisions:
            opportunity_indicators.append(
                "Structured decision resolution offers accountability improvement opportunity"
            )

        if not (context.open_decisions or context.open_dependencies or context.overdue_actions):
            summary = "No active governance signals detected; baseline maintenance is the current priority."
        else:
            parts = []
            if context.open_decisions:
                parts.append(f"{len(context.open_decisions)} open decision(s)")
            if context.open_dependencies:
                parts.append(f"{len(context.open_dependencies)} dependency exception(s)")
            if context.overdue_actions:
                parts.append(f"{len(context.overdue_actions)} overdue commitment(s)")
            summary = f"Current charter shows {', '.join(parts)}."

        return SituationAssessment(
            observations=tuple(observations),
            risk_indicators=tuple(risk_indicators),
            opportunity_indicators=tuple(opportunity_indicators),
            context_summary=summary,
        )


__all__ = ["R2SituationInterpretation"]
