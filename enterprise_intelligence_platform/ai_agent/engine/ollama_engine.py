"""HTTP transport for the Ollama local inference API.

Responsibilities: HTTP request/response only.
All errors are caught and returned as EngineResponse(success=False).
No domain knowledge. No prompt engineering.
"""
from __future__ import annotations

import requests

from enterprise_intelligence_platform.ai_agent.engine.base import BaseInferenceEngine, EngineResponse

_AVAILABILITY_TIMEOUT = 5  # seconds; health-check only, not used for completions


class OllamaEngine(BaseInferenceEngine):
    """Transport for Ollama's /api/generate endpoint (non-streaming)."""

    def __init__(self, base_url: str, model: str, timeout: int = 30) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        timeout: int | None = None,
    ) -> EngineResponse:
        effective_timeout = timeout if timeout is not None else self._timeout
        payload: dict[str, object] = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            resp = requests.post(
                f"{self._base_url}/api/generate",
                json=payload,
                timeout=effective_timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            text: str = data.get("response", "")
            if not text:
                return EngineResponse(
                    text="", success=False, error="Ollama returned empty response field"
                )
            return EngineResponse(text=text, success=True)

        except requests.exceptions.Timeout:
            return EngineResponse(text="", success=False, error="Ollama request timed out")
        except requests.exceptions.ConnectionError as exc:
            return EngineResponse(text="", success=False, error=f"Ollama connection failed: {exc}")
        except requests.exceptions.HTTPError as exc:
            return EngineResponse(text="", success=False, error=f"Ollama HTTP error: {exc}")
        except (ValueError, KeyError) as exc:
            return EngineResponse(text="", success=False, error=f"Ollama response parse error: {exc}")
        except Exception as exc:  # last-resort; engine must never raise
            return EngineResponse(text="", success=False, error=f"Ollama unexpected error: {exc}")

    def is_available(self) -> bool:
        try:
            resp = requests.get(
                f"{self._base_url}/api/tags",
                timeout=_AVAILABILITY_TIMEOUT,
            )
            return resp.status_code == 200
        except Exception:
            return False

    @property
    def identifier(self) -> str:
        return f"ollama:{self._model}"


__all__ = ["OllamaEngine"]
