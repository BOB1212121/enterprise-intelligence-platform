"""R4 — Option Generation.

Maps each CausalHypothesis to a DecisionOption, adding trade-offs,
risk exposure, dependency implications, and verification parameters.
R4 is fully deterministic in Slice 1 (no engine dependency).

No confidence scoring — that is R5's responsibility.
"""
from __future__ import annotations

from enterprise_intelligence_platform.ai_agent.reasoning.base import BaseReasoningLayer
from enterprise_intelligence_platform.ai_agent.schemas import CausalHypothesis, DecisionOption

_MAX_OPTIONS = 3


class R4OptionGeneration(BaseReasoningLayer):
    """Generate decision options from causal hypotheses."""

    def execute(self, hypotheses: list[CausalHypothesis]) -> list[DecisionOption]:
        return [self._hypothesis_to_option(h) for h in hypotheses[:_MAX_OPTIONS]]

    # ── deterministic option construction ────────────────────────────────────

    def _hypothesis_to_option(self, hyp: CausalHypothesis) -> DecisionOption:
        return DecisionOption(
            hypothesis=hyp,
            recommendation_class=hyp.recommendation_class,
            objective_served=hyp.expected_outcome,
            expected_value_hypothesis=hyp.value_effect,
            trade_offs=(
                "Requires dedicated governance time and sustained team commitment.",
                "Behavioural change may need reinforcement across multiple review cycles.",
            ),
            risk_exposure=(
                "Low to Medium — adoption risk mitigated by review-first governance discipline"
            ),
            dependency_implications=(
                "No new dependencies introduced; leverages existing governance structures"
            ),
            owner_and_review_point=(
                "EIP Workflow Owner — review outcome after first full execution cycle"
            ),
            verification_baseline="Charter baseline KPI values at time of decision commitment",
            verification_kpi_direction="Decrease",
            verification_review_window="2 weeks",
            verification_acceptance_criteria=hyp.expected_outcome,
        )


__all__ = ["R4OptionGeneration"]
