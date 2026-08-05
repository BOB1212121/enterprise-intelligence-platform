"""R6 — Decision Support Synthesis.

Ranks CalibratedDecisionOptions by confidence band and constructs
the final RecommendationPackage. R6 is the only layer that instantiates
Recommendation objects.

Any option that fails Recommendation schema validation is silently skipped —
R6 never fails the package due to a single malformed option.
"""
from __future__ import annotations

from enterprise_intelligence_platform.ai_agent.reasoning.base import BaseReasoningLayer
from enterprise_intelligence_platform.ai_agent.schemas import (
    CalibratedDecisionOption,
    ConfidenceState,
    Recommendation,
    RecommendationPackage,
    VerificationPlan,
)
from typing import Any

_BAND_RANK: dict[str, int] = {"High": 3, "Medium": 2, "Low": 1}


class R6DecisionSupportSynthesis(BaseReasoningLayer):
    """Rank calibrated options and assemble the final RecommendationPackage."""

    def execute(
        self,
        options: list[CalibratedDecisionOption],
        charter_name: str,
        context_snapshot: dict[str, Any],
        model_identifier: str,
        fallback_used: bool,
        execution_timestamp: str,
    ) -> RecommendationPackage:
        sorted_opts = sorted(
            options,
            key=lambda o: _BAND_RANK.get(o.confidence_band, 0),
            reverse=True,
        )
        recommendations: list[Recommendation] = []
        for i, opt in enumerate(sorted_opts):
            try:
                recommendations.append(self._to_recommendation(opt, i))
            except (ValueError, TypeError):
                continue  # schema violation on a single option must not break the package

        return RecommendationPackage(
            charter_name=charter_name,
            recommendations=recommendations,
            context_snapshot=context_snapshot,
            model_identifier=model_identifier,
            fallback_used=fallback_used,
            execution_timestamp=execution_timestamp,
        )

    # ── recommendation construction ───────────────────────────────────────────

    def _to_recommendation(self, calibrated: CalibratedDecisionOption, index: int) -> Recommendation:
        opt = calibrated.option
        hyp = opt.hypothesis
        return Recommendation(
            index=index,
            recommendation_class=opt.recommendation_class,
            objective_served=opt.objective_served,
            assumptions=(hyp.assumption,),
            expected_value_hypothesis=opt.expected_value_hypothesis,
            trade_offs=opt.trade_offs,
            risk_exposure=opt.risk_exposure,
            dependency_implications=opt.dependency_implications,
            confidence_state=ConfidenceState(
                band=calibrated.confidence_band,
                rationale=calibrated.confidence_rationale,
                dimensions=dict(calibrated.confidence_dimensions),
            ),
            verification_plan=VerificationPlan(
                baseline=opt.verification_baseline,
                expected_kpi_direction=opt.verification_kpi_direction,
                review_window=opt.verification_review_window,
                acceptance_criteria=opt.verification_acceptance_criteria,
            ),
            owner_and_review_point=opt.owner_and_review_point,
            causal_hypothesis=hyp.hypothesis_text,
        )


__all__ = ["R6DecisionSupportSynthesis"]
