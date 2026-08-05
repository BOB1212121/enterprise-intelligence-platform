"""R1 — Intent Framing.

Converts a CharterContext into an IntentFrame (objective, constraints,
priorities, scope summary). R1 is the first layer to contact the engine.

Fallback: constructs IntentFrame directly from CharterContext fields.
"""
from __future__ import annotations

from enterprise_intelligence_platform.ai_agent.engine.base import BaseInferenceEngine
from enterprise_intelligence_platform.ai_agent.reasoning.base import BaseReasoningLayer
from enterprise_intelligence_platform.ai_agent.schemas import CharterContext, IntentFrame


class R1IntentFraming(BaseReasoningLayer):
    """Extract governance intent from a charter context."""

    def execute(self, context: CharterContext, engine: BaseInferenceEngine) -> IntentFrame:
        response = engine.complete(self._build_prompt(context))
        if response.success:
            parsed = self._parse_llm_output(response.text, context)
            if parsed is not None:
                return parsed
        return self._fallback(context)

    # ── prompt ───────────────────────────────────────────────────────────────

    def _build_prompt(self, context: CharterContext) -> str:
        return (
            "Analyse this governance charter and extract the intent as JSON.\n\n"
            f"Objective: {context.business_objective}\n"
            f"Scope: {context.in_scope_definition}\n\n"
            "Reply with ONLY valid JSON containing:\n"
            '  "objective": one-sentence governance objective (string),\n'
            '  "constraints": list of constraint strings,\n'
            '  "priorities": list of priority strings,\n'
            '  "scope_summary": brief scope description (string).'
        )

    # ── LLM output parsing ────────────────────────────────────────────────────

    def _parse_llm_output(self, text: str, context: CharterContext) -> IntentFrame | None:
        data = self._try_parse_json(text)
        if not isinstance(data, dict):
            return None
        try:
            objective = str(data.get("objective") or "").strip()
            scope_summary = str(data.get("scope_summary") or "").strip()
            if not objective or not scope_summary:
                return None
            constraints = tuple(str(c) for c in (data.get("constraints") or []) if c)
            priorities = tuple(str(p) for p in (data.get("priorities") or []) if p)
            return IntentFrame(
                objective=objective,
                constraints=constraints or ("No explicit constraints identified",),
                priorities=priorities or ("Maintain governance review cadence",),
                scope_summary=scope_summary,
            )
        except (TypeError, ValueError):
            return None

    # ── deterministic fallback ────────────────────────────────────────────────

    def _fallback(self, context: CharterContext) -> IntentFrame:
        constraints: list[str] = []
        critical_deps = [d for d in context.open_dependencies if d.criticality == "Critical"]
        if critical_deps:
            constraints.append(
                f"{len(critical_deps)} critical dependency exception(s) must be resolved before commitment"
            )
        if context.overdue_actions:
            constraints.append(
                f"{len(context.overdue_actions)} overdue commitment(s) require immediate attention"
            )

        priorities: list[str] = []
        high_decisions = [d for d in context.open_decisions if d.criticality == "High"]
        if high_decisions:
            priorities.append(f"Resolve {len(high_decisions)} high-criticality open decision(s)")
        at_risk = [d for d in context.open_dependencies if d.status == "At Risk"]
        if at_risk:
            priorities.append(f"Mitigate {len(at_risk)} at-risk dependency exception(s)")

        return IntentFrame(
            objective=context.business_objective,
            constraints=tuple(constraints) if constraints else ("No active blocking constraints identified",),
            priorities=tuple(priorities) if priorities else ("Maintain governance review cadence",),
            scope_summary=context.in_scope_definition,
        )


__all__ = ["R1IntentFraming"]
