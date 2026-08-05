"""Abstract base class and response contract for all inference engines.

No Frappe dependencies. No domain knowledge. Transport contract only.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class EngineResponse:
    """Immutable result of one inference engine call.

    Callers check ``success`` before using ``text``.
    A failed response always carries a non-empty ``error`` description
    so reasoning layers can log or surface the root cause without raising.
    """

    text: str
    success: bool
    error: str = field(default="")

    def __post_init__(self) -> None:
        if self.success and not self.text:
            raise ValueError("successful EngineResponse must have non-empty text")
        if not self.success and not self.error:
            raise ValueError("failed EngineResponse must have non-empty error")


class BaseInferenceEngine(ABC):
    """Transport-only interface for LLM inference.

    Responsibilities:
      - send a prompt string to an inference backend,
      - return an EngineResponse (never raise),
      - report availability.

    Forbidden:
      - prompt engineering,
      - domain knowledge,
      - business logic,
      - Frappe dependencies.
    """

    @abstractmethod
    def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        timeout: int | None = None,
    ) -> EngineResponse:
        """Submit ``prompt`` to the inference backend.

        Never raises. On any failure returns ``EngineResponse(success=False, ...)``.
        ``timeout`` overrides the engine's default when provided.
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the engine can currently accept requests."""

    @property
    @abstractmethod
    def identifier(self) -> str:
        """Unique string identifying this engine instance, e.g. 'ollama:llama3.2'."""


__all__ = ["BaseInferenceEngine", "EngineResponse"]
