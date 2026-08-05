"""Tests for ReasoningAgent orchestration.

Pure-Python tests — no Frappe initialisation required.
Run with:  python -m pytest enterprise_intelligence_platform/tests/test_reasoning_agent.py -v
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, call

import pytest

from enterprise_intelligence_platform.ai_agent.agent import ReasoningAgent
from enterprise_intelligence_platform.ai_agent.engine.base import EngineResponse
from enterprise_intelligence_platform.ai_agent.engine.null_engine import NullEngine
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
    REQUIRED_CONFIDENCE_DIMENSIONS,
    CausalHypothesis,
    CalibratedDecisionOption,
    CanonicalDecisionSignal,
    CanonicalDependencySignal,
    CanonicalKPISignal,
    CanonicalActionSignal,
    CharterContext,
    DecisionOption,
    IntentFrame,
    RecommendationPackage,
    SituationAssessment,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _rich_context() -> CharterContext:
    return CharterContext(
        charter_name="LWC-2026-00001",
        business_objective="Reduce decision reversal rate below 8%",
        in_scope_definition="All operational decisions in Q3 2026",
        open_decisions=(
            CanonicalDecisionSignal(
                name="DR-001", state="Draft", criticality="High",
                decision_type="Operational", owner="alice@example.com",
            ),
        ),
        open_dependencies=(
            CanonicalDependencySignal(
                name="DER-001", criticality="Critical", status="At Risk",
                dependency_type="System", days_overdue=5,
            ),
        ),
        kpi_signals=(
            CanonicalKPISignal(kpi_code="DRR", baseline_value=12.0, data_source="ERP"),
        ),
        overdue_actions=(
            CanonicalActionSignal(name="TASK-001", overdue_days=3, owner="alice@example.com"),
        ),
    )


def _empty_context() -> CharterContext:
    return CharterContext(
        charter_name="LWC-2026-00002",
        business_objective="Maintain governance discipline",
        in_scope_definition="Q4 scope",
        open_decisions=(),
        open_dependencies=(),
        kpi_signals=(),
        overdue_actions=(),
    )


def _failing_engine() -> MagicMock:
    eng = MagicMock()
    eng.complete.return_value = EngineResponse(text="", success=False, error="offline")
    eng.identifier = "mock:offline"
    return eng


def _succeeding_engine(response_text: str = '{"x": 1}') -> MagicMock:
    eng = MagicMock()
    eng.complete.return_value = EngineResponse(text=response_text, success=True)
    eng.identifier = "mock:online"
    return eng


def _make_stub_r1(frame: IntentFrame, used_fallback: bool = False) -> MagicMock:
    stub = MagicMock(spec=R1IntentFraming)
    stub.execute.return_value = frame
    stub.used_fallback = used_fallback
    return stub


def _make_stub_r2(assessment: SituationAssessment, used_fallback: bool = False) -> MagicMock:
    stub = MagicMock(spec=R2SituationInterpretation)
    stub.execute.return_value = assessment
    stub.used_fallback = used_fallback
    return stub


def _make_stub_r3(hypotheses: list[CausalHypothesis], used_fallback: bool = False) -> MagicMock:
    stub = MagicMock(spec=R3CausalHypothesisConstruction)
    stub.execute.return_value = hypotheses
    stub.used_fallback = used_fallback
    return stub


def _default_frame() -> IntentFrame:
    return IntentFrame(
        objective="Reduce reversal rate",
        constraints=("Budget limited",),
        priorities=("Resolve open decisions",),
        scope_summary="Q3 scope",
    )


def _default_assessment() -> SituationAssessment:
    return SituationAssessment(
        observations=("2 open decisions",),
        risk_indicators=("critical dep at risk",),
        opportunity_indicators=("KPI baselines ready",),
        context_summary="Charter has active signals.",
    )


def _default_hypothesis() -> CausalHypothesis:
    return CausalHypothesis(
        assumption="Review cadence is low",
        context_conditions="critical dep at risk",
        proposed_action="Introduce weekly review",
        expected_outcome="Reversal rate drops",
        value_effect="Cost savings",
        hypothesis_text="If cadence low + risk \u2192 review \u2192 reversal drops + savings",
        recommendation_class="Corrective",
    )


# ── Standard pipeline ─────────────────────────────────────────────────────────


def test_agent_generate_returns_recommendation_package() -> None:
    agent = ReasoningAgent(engine=NullEngine())
    pkg = agent.generate(_rich_context())
    assert isinstance(pkg, RecommendationPackage)


def test_agent_null_engine_produces_at_least_one_recommendation() -> None:
    agent = ReasoningAgent(engine=NullEngine())
    pkg = agent.generate(_rich_context())
    assert len(pkg.recommendations) >= 1


def test_agent_charter_name_propagated_to_package() -> None:
    ctx = _rich_context()
    agent = ReasoningAgent(engine=NullEngine())
    pkg = agent.generate(ctx)
    assert pkg.charter_name == ctx.charter_name


def test_agent_execution_timestamp_is_iso8601_string() -> None:
    agent = ReasoningAgent(engine=NullEngine())
    pkg = agent.generate(_rich_context())
    # Should parse without error
    ts = datetime.fromisoformat(pkg.execution_timestamp)
    assert ts.tzinfo is not None  # timezone-aware


def test_agent_model_identifier_from_null_engine() -> None:
    agent = ReasoningAgent(engine=NullEngine())
    pkg = agent.generate(_rich_context())
    assert pkg.model_identifier == "null:deterministic"


def test_agent_context_snapshot_is_dict_with_charter_name() -> None:
    ctx = _rich_context()
    agent = ReasoningAgent(engine=NullEngine())
    pkg = agent.generate(ctx)
    assert isinstance(pkg.context_snapshot, dict)
    assert pkg.context_snapshot["charter_name"] == ctx.charter_name


def test_agent_with_empty_context_produces_valid_package() -> None:
    agent = ReasoningAgent(engine=NullEngine())
    pkg = agent.generate(_empty_context())
    assert isinstance(pkg, RecommendationPackage)
    assert len(pkg.recommendations) >= 1


# ── Fallback tracking ─────────────────────────────────────────────────────────


def test_agent_fallback_used_true_when_engine_fails() -> None:
    agent = ReasoningAgent(engine=_failing_engine())
    pkg = agent.generate(_rich_context())
    assert pkg.fallback_used is True


def test_agent_fallback_used_false_when_injected_layers_report_no_fallback() -> None:
    ctx = _rich_context()
    real_r1 = R1IntentFraming()
    real_r2 = R2SituationInterpretation()
    real_r3 = R3CausalHypothesisConstruction()

    # Build valid JSON responses that each layer can parse successfully
    r1_json = (
        '{"objective": "Reduce reversal rate", '
        '"constraints": ["budget"], "priorities": ["resolve"], '
        '"scope_summary": "Q3 scope"}'
    )
    r2_json = (
        '{"observations": ["2 open decisions"], '
        '"risk_indicators": ["dep at risk"], '
        '"opportunity_indicators": ["kpis ready"], '
        '"context_summary": "Active charter."}'
    )
    r3_json = (
        '[{"assumption": "Review cadence low", "context_conditions": "dep at risk", '
        '"proposed_action": "Weekly review", "expected_outcome": "DRR drops", '
        '"value_effect": "Savings", '
        '"hypothesis_text": "If cadence low + dep \u2192 review \u2192 DRR drops + savings", '
        '"recommendation_class": "Corrective"}]'
    )

    # Engine returns valid JSON for each call in sequence
    engine = MagicMock()
    engine.identifier = "mock:test"
    engine.complete.side_effect = [
        EngineResponse(text=r1_json, success=True),
        EngineResponse(text=r2_json, success=True),
        EngineResponse(text=r3_json, success=True),
    ]

    agent = ReasoningAgent(engine=engine, r1=real_r1, r2=real_r2, r3=real_r3)
    pkg = agent.generate(ctx)
    assert pkg.fallback_used is False


def test_agent_partial_fallback_r1_only() -> None:
    """If only R1 uses fallback, fallback_used is True."""
    ctx = _rich_context()
    r1 = R1IntentFraming()
    r2 = R2SituationInterpretation()
    r3 = R3CausalHypothesisConstruction()

    r2_json = (
        '{"observations": ["x"], "risk_indicators": [], '
        '"opportunity_indicators": [], "context_summary": "Active."}'
    )
    r3_json = (
        '[{"assumption": "A", "context_conditions": "ctx", '
        '"proposed_action": "act", "expected_outcome": "out", "value_effect": "val", '
        '"hypothesis_text": "If A + ctx \u2192 act \u2192 out + val", '
        '"recommendation_class": "Corrective"}]'
    )

    engine = MagicMock()
    engine.identifier = "mock:partial"
    # R1 gets failure → fallback; R2 and R3 get valid JSON → no fallback
    engine.complete.side_effect = [
        EngineResponse(text="", success=False, error="timeout"),
        EngineResponse(text=r2_json, success=True),
        EngineResponse(text=r3_json, success=True),
    ]

    agent = ReasoningAgent(engine=engine, r1=r1, r2=r2, r3=r3)
    pkg = agent.generate(ctx)
    assert pkg.fallback_used is True


# ── Dependency injection ──────────────────────────────────────────────────────


def test_agent_uses_injected_engine() -> None:
    mock_engine = MagicMock()
    mock_engine.complete.return_value = EngineResponse(text="", success=False, error="x")
    mock_engine.identifier = "injected:test"

    agent = ReasoningAgent(engine=mock_engine)
    pkg = agent.generate(_rich_context())
    assert pkg.model_identifier == "injected:test"
    # Engine must have been called (at least for R1)
    mock_engine.complete.assert_called()


def test_agent_uses_injected_r1_layer() -> None:
    custom_frame = IntentFrame(
        objective="Custom objective",
        constraints=("Custom constraint",),
        priorities=("Custom priority",),
        scope_summary="Custom scope",
    )
    stub_r1 = _make_stub_r1(custom_frame, used_fallback=False)
    agent = ReasoningAgent(engine=NullEngine(), r1=stub_r1)
    pkg = agent.generate(_rich_context())

    stub_r1.execute.assert_called_once()
    assert isinstance(pkg, RecommendationPackage)


def test_agent_r1_through_r3_called_in_order() -> None:
    ctx = _rich_context()
    call_order: list[str] = []

    def record(layer_name: str, real_layer):
        stub = MagicMock(spec=type(real_layer))
        original = real_layer.execute

        def recording_execute(*args, **kwargs):
            call_order.append(layer_name)
            return original(*args, **kwargs)

        stub.execute.side_effect = recording_execute
        stub.used_fallback = False
        return stub

    r1 = R1IntentFraming()
    r2 = R2SituationInterpretation()
    r3 = R3CausalHypothesisConstruction()

    sr1 = record("r1", r1)
    sr2 = record("r2", r2)
    sr3 = record("r3", r3)

    agent = ReasoningAgent(engine=NullEngine(), r1=sr1, r2=sr2, r3=sr3)
    agent.generate(ctx)

    assert call_order == ["r1", "r2", "r3"]


def test_agent_creates_default_layers_when_none_injected() -> None:
    agent = ReasoningAgent(engine=NullEngine())
    assert isinstance(agent._r1, R1IntentFraming)
    assert isinstance(agent._r2, R2SituationInterpretation)
    assert isinstance(agent._r3, R3CausalHypothesisConstruction)
    assert isinstance(agent._r4, R4OptionGeneration)
    assert isinstance(agent._r5, R5ConfidenceCalibration)
    assert isinstance(agent._r6, R6DecisionSupportSynthesis)


def test_agent_injected_layers_are_used_not_replaced() -> None:
    my_r4 = R4OptionGeneration()
    my_r5 = R5ConfidenceCalibration()
    agent = ReasoningAgent(engine=NullEngine(), r4=my_r4, r5=my_r5)
    assert agent._r4 is my_r4
    assert agent._r5 is my_r5


# ── OllamaEngine (mocked) ─────────────────────────────────────────────────────


def test_agent_with_mocked_ollama_success_uses_llm_output() -> None:
    ctx = _rich_context()
    r1_json = (
        '{"objective": "LLM-derived objective", '
        '"constraints": ["c1"], "priorities": ["p1"], '
        '"scope_summary": "LLM scope"}'
    )
    r2_json = (
        '{"observations": ["llm obs"], "risk_indicators": ["llm risk"], '
        '"opportunity_indicators": ["llm opp"], "context_summary": "LLM summary."}'
    )
    r3_json = (
        '[{"assumption": "LLM assumption", "context_conditions": "ctx", '
        '"proposed_action": "LLM action", "expected_outcome": "LLM outcome", '
        '"value_effect": "LLM value", '
        '"hypothesis_text": "If LLM assumption + ctx \u2192 LLM action \u2192 LLM outcome + LLM value", '
        '"recommendation_class": "Optimizing"}]'
    )
    engine = MagicMock()
    engine.identifier = "ollama:llama3.2"
    engine.complete.side_effect = [
        EngineResponse(text=r1_json, success=True),
        EngineResponse(text=r2_json, success=True),
        EngineResponse(text=r3_json, success=True),
    ]

    agent = ReasoningAgent(engine=engine)
    pkg = agent.generate(ctx)

    assert pkg.model_identifier == "ollama:llama3.2"
    assert pkg.fallback_used is False
    assert any("LLM assumption" in r.assumptions[0] for r in pkg.recommendations)


def test_agent_with_failing_ollama_falls_back_gracefully() -> None:
    agent = ReasoningAgent(engine=_failing_engine())
    pkg = agent.generate(_rich_context())
    assert isinstance(pkg, RecommendationPackage)
    assert len(pkg.recommendations) >= 1
    assert pkg.fallback_used is True


# ── Metadata correctness ──────────────────────────────────────────────────────


def test_agent_model_identifier_matches_engine() -> None:
    engine = MagicMock()
    engine.complete.return_value = EngineResponse(text="", success=False, error="x")
    engine.identifier = "test:custom-model"
    agent = ReasoningAgent(engine=engine)
    pkg = agent.generate(_rich_context())
    assert pkg.model_identifier == "test:custom-model"


def test_agent_fallback_used_propagated_to_package() -> None:
    agent = ReasoningAgent(engine=NullEngine())
    pkg = agent.generate(_rich_context())
    # NullEngine returns non-JSON → fallback always used
    assert isinstance(pkg.fallback_used, bool)
    assert pkg.fallback_used is True


def test_agent_fallback_stub_injection_false() -> None:
    """When all injected stubs report no fallback, package.fallback_used is False."""
    ctx = _rich_context()
    frame = _default_frame()
    assessment = _default_assessment()
    hypotheses = [_default_hypothesis()]

    sr1 = _make_stub_r1(frame, used_fallback=False)
    sr2 = _make_stub_r2(assessment, used_fallback=False)
    sr3 = _make_stub_r3(hypotheses, used_fallback=False)

    agent = ReasoningAgent(engine=NullEngine(), r1=sr1, r2=sr2, r3=sr3)
    pkg = agent.generate(ctx)
    assert pkg.fallback_used is False


def test_agent_fallback_stub_injection_r2_true() -> None:
    """When R2 fallback is True, overall fallback_used is True."""
    ctx = _rich_context()
    frame = _default_frame()
    assessment = _default_assessment()
    hypotheses = [_default_hypothesis()]

    sr1 = _make_stub_r1(frame, used_fallback=False)
    sr2 = _make_stub_r2(assessment, used_fallback=True)
    sr3 = _make_stub_r3(hypotheses, used_fallback=False)

    agent = ReasoningAgent(engine=NullEngine(), r1=sr1, r2=sr2, r3=sr3)
    pkg = agent.generate(ctx)
    assert pkg.fallback_used is True


# ── Recommendation ordering ───────────────────────────────────────────────────


def test_agent_recommendation_indices_are_sequential() -> None:
    agent = ReasoningAgent(engine=NullEngine())
    pkg = agent.generate(_rich_context())
    indices = [r.index for r in pkg.recommendations]
    assert indices == list(range(len(indices)))


def test_agent_recommendations_all_schema_valid() -> None:
    agent = ReasoningAgent(engine=NullEngine())
    pkg = agent.generate(_rich_context())
    for rec in pkg.recommendations:
        assert rec.objective_served
        assert rec.assumptions
        assert "\u2192" in rec.causal_hypothesis
        assert rec.confidence_state.band in {"High", "Medium", "Low"}
        for dim in REQUIRED_CONFIDENCE_DIMENSIONS:
            assert dim in rec.confidence_state.dimensions


# ── Empty / invalid context ───────────────────────────────────────────────────


def test_agent_raises_on_none_context() -> None:
    agent = ReasoningAgent(engine=NullEngine())
    with pytest.raises(TypeError, match="CharterContext"):
        agent.generate(None)  # type: ignore[arg-type]


def test_agent_raises_on_wrong_type_context() -> None:
    agent = ReasoningAgent(engine=NullEngine())
    with pytest.raises(TypeError, match="CharterContext"):
        agent.generate({"charter_name": "x"})  # type: ignore[arg-type]


# ── Determinism ───────────────────────────────────────────────────────────────


def test_agent_null_engine_produces_consistent_structure() -> None:
    """Two NullEngine runs on the same context must produce structurally identical packages."""
    ctx = _rich_context()
    pkg1 = ReasoningAgent(engine=NullEngine()).generate(ctx)
    pkg2 = ReasoningAgent(engine=NullEngine()).generate(ctx)
    assert len(pkg1.recommendations) == len(pkg2.recommendations)
    classes1 = [r.recommendation_class for r in pkg1.recommendations]
    classes2 = [r.recommendation_class for r in pkg2.recommendations]
    assert classes1 == classes2


# ── Engine factory (default engine path) ─────────────────────────────────────


def test_agent_default_engine_resolved_from_factory() -> None:
    """When no engine is injected, the factory must be called inside generate()."""
    import frappe
    from unittest.mock import patch

    conf = MagicMock()
    conf.get = lambda key, default=None: default  # all defaults → NullEngine
    with patch.object(frappe, "conf", conf):
        agent = ReasoningAgent()  # no engine injected
        pkg = agent.generate(_rich_context())
    assert isinstance(pkg, RecommendationPackage)
    assert pkg.model_identifier == "null:deterministic"
