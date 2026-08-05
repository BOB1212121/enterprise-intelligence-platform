"""R3 — Causal Hypothesis Construction.

Transforms a SituationAssessment into 1–3 CausalHypothesis objects.
Each hypothesis follows the approved grammar:
  'If [assumption] + [context_conditions] → [action] → [outcome] + [value_effect]'

R3 is the last layer that contacts the inference engine.
R4, R5, and R6 are deterministic in Slice 1.

Fallback: derives canonical hypotheses from risk and opportunity signals.
"""
from __future__ import annotations

from enterprise_intelligence_platform.ai_agent.engine.base import BaseInferenceEngine
from enterprise_intelligence_platform.ai_agent.reasoning.base import BaseReasoningLayer
from enterprise_intelligence_platform.ai_agent.schemas import (
    VALID_RECOMMENDATION_CLASSES,
    CausalHypothesis,
    SituationAssessment,
)

_MAX_HYPOTHESES = 3


class R3CausalHypothesisConstruction(BaseReasoningLayer):
    """Generate causal hypotheses from the governance situation."""

    def execute(
        self,
        assessment: SituationAssessment,
        engine: BaseInferenceEngine,
    ) -> list[CausalHypothesis]:
        response = engine.complete(self._build_prompt(assessment))
        if response.success:
            parsed = self._parse_llm_output(response.text, assessment)
            if parsed:
                return parsed
        return self._fallback(assessment)

    # ── prompt ───────────────────────────────────────────────────────────────

    def _build_prompt(self, assessment: SituationAssessment) -> str:
        obs_lines = "\n".join(f"- {o}" for o in assessment.observations[:5])
        risk_lines = "\n".join(f"- {r}" for r in assessment.risk_indicators[:3])
        return (
            "Generate 1–3 governance causal hypotheses. "
            "Use this grammar exactly for hypothesis_text:\n"
            "  'If [assumption] + [context] \u2192 [action] \u2192 [outcome] + [value effect]'\n\n"
            f"Situation: {assessment.context_summary}\n"
            f"Observations:\n{obs_lines}\n"
            f"Risk indicators:\n{risk_lines}\n\n"
            "Reply with ONLY a valid JSON array. Each item must have:\n"
            "  assumption, context_conditions, proposed_action, expected_outcome,\n"
            "  value_effect, hypothesis_text (must contain \u2192),\n"
            "  recommendation_class (Preventive | Corrective | Optimizing | Learning-Oriented)."
        )

    # ── LLM output parsing ────────────────────────────────────────────────────

    def _parse_llm_output(
        self,
        text: str,
        assessment: SituationAssessment,
    ) -> list[CausalHypothesis] | None:
        data = self._try_parse_json(text)
        # Accept {"hypotheses": [...]} wrapper or bare array
        if isinstance(data, dict):
            data = data.get("hypotheses") or data.get("causal_hypotheses") or []
        if not isinstance(data, list) or not data:
            return None

        hypotheses: list[CausalHypothesis] = []
        for item in data[:_MAX_HYPOTHESES]:
            if not isinstance(item, dict):
                continue
            hypothesis_text = str(item.get("hypothesis_text") or "").strip()
            if "\u2192" not in hypothesis_text:
                continue
            assumption = str(item.get("assumption") or "").strip()
            proposed_action = str(item.get("proposed_action") or "").strip()
            if not assumption or not proposed_action:
                continue
            rec_class = str(item.get("recommendation_class") or "Corrective").strip()
            if rec_class not in VALID_RECOMMENDATION_CLASSES:
                rec_class = "Corrective"
            try:
                hypotheses.append(
                    CausalHypothesis(
                        assumption=assumption,
                        context_conditions=(
                            str(item.get("context_conditions") or "").strip()
                            or assessment.context_summary
                        ),
                        proposed_action=proposed_action,
                        expected_outcome=(
                            str(item.get("expected_outcome") or "").strip()
                            or "Governance outcomes improve"
                        ),
                        value_effect=(
                            str(item.get("value_effect") or "").strip()
                            or "Reduced reversal and rework cost"
                        ),
                        hypothesis_text=hypothesis_text,
                        recommendation_class=rec_class,
                    )
                )
            except (TypeError, ValueError):
                continue

        return hypotheses if hypotheses else None

    # ── deterministic fallback ────────────────────────────────────────────────

    def _fallback(self, assessment: SituationAssessment) -> list[CausalHypothesis]:
        hypotheses: list[CausalHypothesis] = []

        if assessment.risk_indicators:
            risk = assessment.risk_indicators[0]
            hypotheses.append(
                CausalHypothesis(
                    assumption="Current governance review cadence is insufficient to address active risk signals",
                    context_conditions=risk,
                    proposed_action="Introduce a structured governance review cadence focused on risk resolution",
                    expected_outcome="Active risk indicators are resolved within two governance cycles",
                    value_effect="Reduced decision reversal rate and lower rework cost",
                    hypothesis_text=(
                        f"If governance review cadence is insufficient + {risk} "
                        "\u2192 introduce structured risk-focused governance review "
                        "\u2192 risk indicators resolved + reduced reversal rate"
                    ),
                    recommendation_class="Corrective",
                )
            )

        if assessment.opportunity_indicators and len(hypotheses) < _MAX_HYPOTHESES:
            opp = assessment.opportunity_indicators[0]
            hypotheses.append(
                CausalHypothesis(
                    assumption="Existing governance baselines can be leveraged for measurable improvement",
                    context_conditions=opp,
                    proposed_action="Align decisions to measurable KPI improvement targets",
                    expected_outcome="KPI movement is attributable and governance-accountable",
                    value_effect="Improved value attribution credibility and decision confidence",
                    hypothesis_text=(
                        f"If governance baselines are underutilised + {opp} "
                        "\u2192 align decisions to measurable KPI improvement targets "
                        "\u2192 attributable outcome improvement + increased governance confidence"
                    ),
                    recommendation_class="Optimizing",
                )
            )

        if not hypotheses:
            hypotheses.append(
                CausalHypothesis(
                    assumption="Decision governance discipline can be improved through structured review",
                    context_conditions=assessment.context_summary,
                    proposed_action="Establish a weekly decision governance review ritual",
                    expected_outcome="Decision accountability and stakeholder confidence improve measurably",
                    value_effect="Lower decision reversal rate and reduced strategic drift",
                    hypothesis_text=(
                        f"If decision governance lacks structured review + {assessment.context_summary} "
                        "\u2192 establish weekly governance review ritual "
                        "\u2192 decision accountability improves + reversal rate decreases"
                    ),
                    recommendation_class="Preventive",
                )
            )

        return hypotheses


__all__ = ["R3CausalHypothesisConstruction"]
