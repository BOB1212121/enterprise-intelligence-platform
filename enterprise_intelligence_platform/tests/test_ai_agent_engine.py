"""Tests for the ai_agent/engine package.

Pure-Python tests — no Frappe initialisation required.
Run with:  python -m pytest enterprise_intelligence_platform/tests/test_ai_agent_engine.py -v
"""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

from enterprise_intelligence_platform.ai_agent.engine import (
    NullEngine,
    OllamaEngine,
    get_engine,
)
from enterprise_intelligence_platform.ai_agent.engine.base import (
    BaseInferenceEngine,
    EngineResponse,
)

# ── EngineResponse ─────────────────────────────────────────────────────────────


def test_engine_response_success_requires_non_empty_text() -> None:
    with pytest.raises(ValueError, match="non-empty text"):
        EngineResponse(text="", success=True)


def test_engine_response_failure_requires_non_empty_error() -> None:
    with pytest.raises(ValueError, match="non-empty error"):
        EngineResponse(text="", success=False, error="")


def test_engine_response_success_is_frozen() -> None:
    resp = EngineResponse(text="hello", success=True)
    with pytest.raises((AttributeError, TypeError)):
        resp.text = "other"  # type: ignore[misc]


def test_engine_response_valid_success() -> None:
    resp = EngineResponse(text="result", success=True)
    assert resp.success
    assert resp.text == "result"
    assert resp.error == ""


def test_engine_response_valid_failure() -> None:
    resp = EngineResponse(text="", success=False, error="timed out")
    assert not resp.success
    assert resp.error == "timed out"
    assert resp.text == ""


# ── BaseInferenceEngine ────────────────────────────────────────────────────────


def test_base_engine_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        BaseInferenceEngine()  # type: ignore[abstract]


def test_base_engine_subclass_must_implement_complete() -> None:
    class Partial(BaseInferenceEngine):
        def is_available(self) -> bool:
            return True

        @property
        def identifier(self) -> str:
            return "partial"

    with pytest.raises(TypeError):
        Partial()  # type: ignore[abstract]


def test_base_engine_subclass_must_implement_is_available() -> None:
    class Partial(BaseInferenceEngine):
        def complete(self, prompt: str, system_prompt: str = "", timeout: int | None = None) -> EngineResponse:
            return EngineResponse(text="x", success=True)

        @property
        def identifier(self) -> str:
            return "partial"

    with pytest.raises(TypeError):
        Partial()  # type: ignore[abstract]


def test_base_engine_subclass_must_implement_identifier() -> None:
    class Partial(BaseInferenceEngine):
        def complete(self, prompt: str, system_prompt: str = "", timeout: int | None = None) -> EngineResponse:
            return EngineResponse(text="x", success=True)

        def is_available(self) -> bool:
            return True

    with pytest.raises(TypeError):
        Partial()  # type: ignore[abstract]


# ── NullEngine ─────────────────────────────────────────────────────────────────


def test_null_engine_complete_returns_success() -> None:
    engine = NullEngine()
    resp = engine.complete("any prompt")
    assert resp.success is True


def test_null_engine_complete_returns_non_empty_text() -> None:
    engine = NullEngine()
    resp = engine.complete("any prompt")
    assert resp.text


def test_null_engine_complete_is_deterministic() -> None:
    engine = NullEngine()
    r1 = engine.complete("prompt A")
    r2 = engine.complete("prompt B")
    assert r1.text == r2.text


def test_null_engine_complete_accepts_system_prompt() -> None:
    engine = NullEngine()
    resp = engine.complete("prompt", system_prompt="system")
    assert resp.success is True


def test_null_engine_complete_accepts_timeout_override() -> None:
    engine = NullEngine()
    resp = engine.complete("prompt", timeout=1)
    assert resp.success is True


def test_null_engine_is_always_available() -> None:
    assert NullEngine().is_available() is True


def test_null_engine_identifier() -> None:
    assert NullEngine().identifier == "null:deterministic"


def test_null_engine_is_instance_of_base() -> None:
    assert isinstance(NullEngine(), BaseInferenceEngine)


def test_null_engine_never_raises() -> None:
    engine = NullEngine()
    # Should not raise for empty prompt, whitespace, or very long inputs
    for prompt in ("", " ", "x" * 10_000):
        resp = engine.complete(prompt)
        assert resp.success is True


# ── OllamaEngine helpers ───────────────────────────────────────────────────────


def _make_requests_response(status: int = 200, body: Any = None) -> MagicMock:
    """Build a mock requests.Response."""
    mock_resp = MagicMock(spec=requests.Response)
    mock_resp.status_code = status
    if status >= 400:
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_resp
        )
    else:
        mock_resp.raise_for_status.return_value = None
    if body is not None:
        mock_resp.json.return_value = body
    else:
        mock_resp.json.return_value = {}
    return mock_resp


# ── OllamaEngine.complete ──────────────────────────────────────────────────────


def test_ollama_engine_success() -> None:
    engine = OllamaEngine(base_url="http://localhost:11434", model="llama3.2")
    mock_resp = _make_requests_response(200, {"response": "generated text"})
    with patch("requests.post", return_value=mock_resp):
        result = engine.complete("hello")
    assert result.success is True
    assert result.text == "generated text"
    assert result.error == ""


def test_ollama_engine_includes_system_prompt_in_payload() -> None:
    engine = OllamaEngine(base_url="http://localhost:11434", model="llama3.2")
    mock_resp = _make_requests_response(200, {"response": "ok"})
    captured: list[dict] = []

    def mock_post(url: str, json: dict, timeout: int) -> MagicMock:
        captured.append(json)
        return mock_resp

    with patch("requests.post", side_effect=mock_post):
        engine.complete("prompt", system_prompt="you are helpful")

    assert captured[0].get("system") == "you are helpful"


def test_ollama_engine_per_call_timeout_overrides_default() -> None:
    engine = OllamaEngine(base_url="http://localhost:11434", model="llama3.2", timeout=30)
    mock_resp = _make_requests_response(200, {"response": "ok"})
    captured_timeouts: list[int] = []

    def mock_post(url: str, json: dict, timeout: int) -> MagicMock:
        captured_timeouts.append(timeout)
        return mock_resp

    with patch("requests.post", side_effect=mock_post):
        engine.complete("prompt", timeout=5)

    assert captured_timeouts[0] == 5


def test_ollama_engine_uses_default_timeout_when_none() -> None:
    engine = OllamaEngine(base_url="http://localhost:11434", model="llama3.2", timeout=99)
    mock_resp = _make_requests_response(200, {"response": "ok"})
    captured_timeouts: list[int] = []

    def mock_post(url: str, json: dict, timeout: int) -> MagicMock:
        captured_timeouts.append(timeout)
        return mock_resp

    with patch("requests.post", side_effect=mock_post):
        engine.complete("prompt")

    assert captured_timeouts[0] == 99


def test_ollama_engine_connection_error_returns_failure() -> None:
    engine = OllamaEngine(base_url="http://localhost:11434", model="llama3.2")
    with patch("requests.post", side_effect=requests.exceptions.ConnectionError("refused")):
        result = engine.complete("prompt")
    assert result.success is False
    assert "connection failed" in result.error.lower()


def test_ollama_engine_timeout_returns_failure() -> None:
    engine = OllamaEngine(base_url="http://localhost:11434", model="llama3.2")
    with patch("requests.post", side_effect=requests.exceptions.Timeout()):
        result = engine.complete("prompt")
    assert result.success is False
    assert "timed out" in result.error.lower()


def test_ollama_engine_http_error_returns_failure() -> None:
    engine = OllamaEngine(base_url="http://localhost:11434", model="llama3.2")
    mock_resp = _make_requests_response(status=500, body={})
    with patch("requests.post", return_value=mock_resp):
        result = engine.complete("prompt")
    assert result.success is False
    assert "http error" in result.error.lower()


def test_ollama_engine_empty_response_field_returns_failure() -> None:
    engine = OllamaEngine(base_url="http://localhost:11434", model="llama3.2")
    mock_resp = _make_requests_response(200, {"response": ""})
    with patch("requests.post", return_value=mock_resp):
        result = engine.complete("prompt")
    assert result.success is False
    assert "empty" in result.error.lower()


def test_ollama_engine_missing_response_field_returns_failure() -> None:
    engine = OllamaEngine(base_url="http://localhost:11434", model="llama3.2")
    mock_resp = _make_requests_response(200, {"something_else": "data"})
    with patch("requests.post", return_value=mock_resp):
        result = engine.complete("prompt")
    assert result.success is False


def test_ollama_engine_invalid_json_returns_failure() -> None:
    engine = OllamaEngine(base_url="http://localhost:11434", model="llama3.2")
    mock_resp = MagicMock(spec=requests.Response)
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.side_effect = ValueError("not json")
    with patch("requests.post", return_value=mock_resp):
        result = engine.complete("prompt")
    assert result.success is False
    assert "parse error" in result.error.lower()


def test_ollama_engine_unexpected_exception_returns_failure() -> None:
    engine = OllamaEngine(base_url="http://localhost:11434", model="llama3.2")
    with patch("requests.post", side_effect=RuntimeError("unexpected")):
        result = engine.complete("prompt")
    assert result.success is False
    assert "unexpected" in result.error.lower()


# ── OllamaEngine.is_available ──────────────────────────────────────────────────


def test_ollama_engine_is_available_when_server_responds_200() -> None:
    engine = OllamaEngine(base_url="http://localhost:11434", model="llama3.2")
    mock_resp = MagicMock(spec=requests.Response)
    mock_resp.status_code = 200
    with patch("requests.get", return_value=mock_resp):
        assert engine.is_available() is True


def test_ollama_engine_not_available_when_server_responds_non_200() -> None:
    engine = OllamaEngine(base_url="http://localhost:11434", model="llama3.2")
    mock_resp = MagicMock(spec=requests.Response)
    mock_resp.status_code = 503
    with patch("requests.get", return_value=mock_resp):
        assert engine.is_available() is False


def test_ollama_engine_not_available_on_connection_error() -> None:
    engine = OllamaEngine(base_url="http://localhost:11434", model="llama3.2")
    with patch("requests.get", side_effect=requests.exceptions.ConnectionError()):
        assert engine.is_available() is False


def test_ollama_engine_not_available_on_timeout() -> None:
    engine = OllamaEngine(base_url="http://localhost:11434", model="llama3.2")
    with patch("requests.get", side_effect=requests.exceptions.Timeout()):
        assert engine.is_available() is False


def test_ollama_engine_identifier() -> None:
    engine = OllamaEngine(base_url="http://localhost:11434", model="mistral")
    assert engine.identifier == "ollama:mistral"


def test_ollama_engine_strips_trailing_slash_from_base_url() -> None:
    engine = OllamaEngine(base_url="http://localhost:11434/", model="llama3.2")
    mock_resp = _make_requests_response(200, {"response": "ok"})
    captured_urls: list[str] = []

    def mock_post(url: str, json: dict, timeout: int) -> MagicMock:
        captured_urls.append(url)
        return mock_resp

    with patch("requests.post", side_effect=mock_post):
        engine.complete("prompt")

    assert not captured_urls[0].startswith("http://localhost:11434//")


# ── Engine factory ─────────────────────────────────────────────────────────────


def _make_mock_conf(values: dict[str, object]) -> MagicMock:
    conf = MagicMock()
    conf.get = lambda key, default=None: values.get(key, default)
    return conf


def test_factory_defaults_to_null_engine_when_conf_absent() -> None:
    import frappe
    with patch.object(frappe, "conf", None):
        engine = get_engine()
    assert isinstance(engine, NullEngine)


def test_factory_returns_null_engine_when_engine_type_null() -> None:
    import frappe
    conf = _make_mock_conf({"eip_ai_engine": "null"})
    with patch.object(frappe, "conf", conf):
        engine = get_engine()
    assert isinstance(engine, NullEngine)


def test_factory_returns_null_engine_when_engine_type_absent() -> None:
    import frappe
    conf = _make_mock_conf({})
    with patch.object(frappe, "conf", conf):
        engine = get_engine()
    assert isinstance(engine, NullEngine)


def test_factory_returns_null_engine_when_ai_disabled() -> None:
    import frappe
    conf = _make_mock_conf({"eip_ai_enabled": False, "eip_ai_engine": "ollama"})
    with patch.object(frappe, "conf", conf):
        engine = get_engine()
    assert isinstance(engine, NullEngine)


def test_factory_returns_ollama_engine_when_configured() -> None:
    import frappe
    conf = _make_mock_conf({
        "eip_ai_engine": "ollama",
        "eip_ai_base_url": "http://localhost:11434",
        "eip_ai_model": "llama3.2",
        "eip_ai_timeout": 30,
    })
    with patch.object(frappe, "conf", conf):
        engine = get_engine()
    assert isinstance(engine, OllamaEngine)
    assert engine.identifier == "ollama:llama3.2"


def test_factory_applies_configured_model_to_ollama_engine() -> None:
    import frappe
    conf = _make_mock_conf({
        "eip_ai_engine": "ollama",
        "eip_ai_model": "mistral",
    })
    with patch.object(frappe, "conf", conf):
        engine = get_engine()
    assert isinstance(engine, OllamaEngine)
    assert "mistral" in engine.identifier


def test_factory_falls_back_to_null_engine_for_unknown_engine_type() -> None:
    import frappe
    conf = _make_mock_conf({"eip_ai_engine": "gpt5_magic_cloud"})
    with patch.object(frappe, "conf", conf):
        engine = get_engine()
    assert isinstance(engine, NullEngine)


def test_factory_handles_invalid_timeout_gracefully() -> None:
    import frappe
    conf = _make_mock_conf({
        "eip_ai_engine": "ollama",
        "eip_ai_timeout": "not-a-number",
    })
    with patch.object(frappe, "conf", conf):
        engine = get_engine()
    # Should not raise; OllamaEngine created with default timeout
    assert isinstance(engine, OllamaEngine)


def test_factory_returns_null_engine_on_import_error() -> None:
    """When frappe is not importable the factory must not raise."""
    import sys
    original = sys.modules.get("frappe")
    sys.modules["frappe"] = None  # type: ignore[assignment]
    try:
        engine = get_engine()
        assert isinstance(engine, NullEngine)
    finally:
        if original is not None:
            sys.modules["frappe"] = original
        else:
            del sys.modules["frappe"]


def test_factory_creates_new_instance_on_each_call() -> None:
    """Config changes take effect on the next call — no caching."""
    import frappe
    conf = _make_mock_conf({"eip_ai_engine": "null"})
    with patch.object(frappe, "conf", conf):
        e1 = get_engine()
        e2 = get_engine()
    assert e1 is not e2
