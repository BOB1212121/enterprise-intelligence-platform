"""Engine factory. Reads frappe.conf on every call — never cached globally.

Switching eip_ai_engine in frappe.conf takes effect on the next request.
Defaults to NullEngine in all error/missing-config cases so the system
remains functional without LLM infrastructure.
"""
from __future__ import annotations

from enterprise_intelligence_platform.ai_agent.engine.base import BaseInferenceEngine, EngineResponse
from enterprise_intelligence_platform.ai_agent.engine.null_engine import NullEngine
from enterprise_intelligence_platform.ai_agent.engine.ollama_engine import OllamaEngine

_DEFAULT_BASE_URL = "http://localhost:11434"
_DEFAULT_MODEL = "llama3.2"
_DEFAULT_TIMEOUT = 30


def get_engine() -> BaseInferenceEngine:
    """Return a configured engine instance based on the current site config.

    Safe to call outside a Frappe request context — returns NullEngine
    when frappe is uninitialised or config keys are absent.
    """
    engine_type = "null"
    base_url = _DEFAULT_BASE_URL
    model = _DEFAULT_MODEL
    timeout = _DEFAULT_TIMEOUT

    try:
        import frappe  # noqa: PLC0415 — intentional lazy import

        conf = getattr(frappe, "conf", None)
        if conf is not None:
            if not conf.get("eip_ai_enabled", True):
                return NullEngine()
            engine_type = conf.get("eip_ai_engine", "null") or "null"
            base_url = conf.get("eip_ai_base_url", _DEFAULT_BASE_URL) or _DEFAULT_BASE_URL
            model = conf.get("eip_ai_model", _DEFAULT_MODEL) or _DEFAULT_MODEL
            try:
                timeout = int(conf.get("eip_ai_timeout", _DEFAULT_TIMEOUT))
            except (TypeError, ValueError):
                timeout = _DEFAULT_TIMEOUT
    except (ImportError, AttributeError):
        pass

    if engine_type == "ollama":
        return OllamaEngine(base_url=base_url, model=model, timeout=timeout)

    # unknown or missing engine type → safe default
    return NullEngine()


__all__ = [
    "BaseInferenceEngine",
    "EngineResponse",
    "NullEngine",
    "OllamaEngine",
    "get_engine",
]
