"""ReasoningAgent — orchestration only.

Runs a CharterContext through R1 → R6 and returns a RecommendationPackage.

This module contains NO:
  - prompt engineering     (R1–R3)
  - hypothesis logic       (R3)
  - ranking logic          (R6)
  - confidence logic       (R5)
  - parsing logic          (R1–R3 / BaseReasoningLayer)
  - database access
  - Frappe imports
  - HTTP requests

Expected engine/layer failures (timeout, bad LLM output) are handled inside
individual layers and never reach this class.  Unexpected failures (schema
violations, programming errors) are not caught here so that tests fail loudly.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from enterprise_intelligence_platform.ai_agent.engine import get_engine
from enterprise_intelligence_platform.ai_agent.engine.base import BaseInferenceEngine
from enterprise_intelligence_platform.ai_agent.reasoning.r1_intent_framing import R1IntentFraming
from enterprise_intelligence_platform.ai_agent.reasoning.r2_situation_interpretation import (
    R2SituationInterpretation,
)
from enterprise_intelligence_platform.ai_agent.reasoning.r3_causal_hypothesis import (
    R3CausalHypothesisConstruction,
)
from enterprise_intelligence_platform.ai_agent.reasoning.r4_option_generation import R4OptionGeneration
from enterprise_intelligence_platform.ai_agent.reasoning.r5_confidence_calibration import (
    R5ConfidenceCalibration,
)
from enterprise_intelligence_platform.ai_agent.reasoning.r6_synthesis import R6DecisionSupportSynthesis
from enterprise_intelligence_platform.ai_agent.schemas import (
    CharterContext,
    RecommendationPackage,
    charter_context_to_snapshot,
)


class ReasoningAgent:
    """Orchestrates the R1 → R6 reasoning pipeline.

    All constructor parameters accept None (use default) or an injected instance.
    Inject non-default values in tests to avoid touching the factory or Frappe.

    Injected layers must expose a boolean ``used_fallback`` attribute so the
    agent can correctly populate ``RecommendationPackage.fallback_used``.
    """

    def __init__(
        self,
        engine: BaseInferenceEngine | None = None,
        r1: R1IntentFraming | None = None,
        r2: R2SituationInterpretation | None = None,
        r3: R3CausalHypothesisConstruction | None = None,
        r4: R4OptionGeneration | None = None,
        r5: R5ConfidenceCalibration | None = None,
        r6: R6DecisionSupportSynthesis | None = None,
    ) -> None:
        # engine=None means "resolve lazily from factory on each generate() call"
        self._engine = engine
        self._r1 = r1 if r1 is not None else R1IntentFraming()
        self._r2 = r2 if r2 is not None else R2SituationInterpretation()
        self._r3 = r3 if r3 is not None else R3CausalHypothesisConstruction()
        self._r4 = r4 if r4 is not None else R4OptionGeneration()
        self._r5 = r5 if r5 is not None else R5ConfidenceCalibration()
        self._r6 = r6 if r6 is not None else R6DecisionSupportSynthesis()

    def generate(self, context: CharterContext) -> RecommendationPackage:
        """Execute the full R1 → R6 pipeline and return a RecommendationPackage.

        The pipeline runs sequentially; each layer's output is the next layer's input.
        """
        if not isinstance(context, CharterContext):
            raise TypeError(f"context must be a CharterContext, got {type(context).__name__}")

        engine = self._engine if self._engine is not None else get_engine()
        execution_timestamp = datetime.now(timezone.utc).isoformat()
        context_snapshot = charter_context_to_snapshot(context)

        frame = self._r1.execute(context, engine)
        assessment = self._r2.execute(frame, context, engine)
        hypotheses = self._r3.execute(assessment, engine)
        options = self._r4.execute(hypotheses)
        calibrated = self._r5.execute(options)

        fallback_used = bool(
            getattr(self._r1, "used_fallback", False)
            or getattr(self._r2, "used_fallback", False)
            or getattr(self._r3, "used_fallback", False)
        )

        return self._r6.execute(
            options=calibrated,
            charter_name=context.charter_name,
            context_snapshot=context_snapshot,
            model_identifier=engine.identifier,
            fallback_used=fallback_used,
            execution_timestamp=execution_timestamp,
        )


__all__ = ["ReasoningAgent"]
