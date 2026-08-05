"""R5 — Confidence Calibration.

Adds a five-dimension confidence state to each DecisionOption, producing
a CalibratedDecisionOption. R5 is responsible only for confidence —
it does not rank or synthesise recommendations.

R5 is fully deterministic in Slice 1. Slice 2 upgrades it to LLM-assisted
calibration when richer evidence signals are available.
"""
from __future__ import annotations

from enterprise_intelligence_platform.ai_agent.reasoning.base import BaseReasoningLayer
from enterprise_intelligence_platform.ai_agent.schemas import (
    CalibratedDecisionOption,
    DecisionOption,
)

# Deterministic dimension text used when no LLM calibration is available.
_DETERMINISTIC_DIMENSIONS: dict[str, str] = {
    "evidence_strength": "Moderate — derived from observable charter context signals",
    "relevance": "High — directly addresses the charter's governance objective",
    "freshness": "Current — signals reflect the latest charter state at analysis time",
    "transferability": "Context-specific — applicable within this charter's governance domain",
    "contradiction_pressure": "Low — no conflicting signals identified in current context",
}

_DETERMINISTIC_BAND = "Medium"
_DETERMINISTIC_RATIONALE = (
    "Moderate confidence based on observable charter signals. "
    "Higher confidence requires validated outcome evidence from prior governance cycles."
)


class R5ConfidenceCalibration(BaseReasoningLayer):
    """Calibrate confidence for each decision option."""

    def execute(self, options: list[DecisionOption]) -> list[CalibratedDecisionOption]:
        return [self._calibrate(opt) for opt in options]

    # ── deterministic calibration ─────────────────────────────────────────────

    def _calibrate(self, option: DecisionOption) -> CalibratedDecisionOption:
        return CalibratedDecisionOption(
            option=option,
            confidence_band=_DETERMINISTIC_BAND,
            confidence_rationale=_DETERMINISTIC_RATIONALE,
            confidence_dimensions=dict(_DETERMINISTIC_DIMENSIONS),
        )


__all__ = ["R5ConfidenceCalibration"]
