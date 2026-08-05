"""Deterministic inference engine with no external dependencies.

Used when Ollama is unavailable or when eip_ai_engine is not configured.
NullEngine always succeeds; reasoning layers will apply their own deterministic
_fallback() logic when they cannot parse a structured response from the engine.
"""
from __future__ import annotations

from enterprise_intelligence_platform.ai_agent.engine.base import BaseInferenceEngine, EngineResponse

_STUB_TEXT = (
    "[NullEngine: deterministic mode active. "
    "Set eip_ai_engine=ollama in frappe.conf to enable LLM inference.]"
)


class NullEngine(BaseInferenceEngine):
    """Inference engine that never fails and has no external dependencies.

    Thread-safe: stateless; every call returns the same constant response.
    """

    _IDENTIFIER = "null:deterministic"

    def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        timeout: int | None = None,
    ) -> EngineResponse:
        # prompt, system_prompt, and timeout are accepted but intentionally unused
        return EngineResponse(text=_STUB_TEXT, success=True)

    def is_available(self) -> bool:
        return True

    @property
    def identifier(self) -> str:
        return self._IDENTIFIER


__all__ = ["NullEngine"]
