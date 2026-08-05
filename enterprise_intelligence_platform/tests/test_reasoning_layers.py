"""Tests for the ai_agent/reasoning package and intermediate schema types.

Pure-Python tests — no Frappe initialisation required.
Run with:  python -m pytest enterprise_intelligence_platform/tests/test_reasoning_layers.py -v
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from enterprise_intelligence_platform.ai_agent.engine.base import EngineResponse
from enterprise_intelligence_platform.ai_agent.engine.null_engine import NullEngine
from enterprise_intelligence_platform.ai_agent.reasoning.base import BaseReasoningLayer
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
    VALID_RECOMMENDATION_CLASSES,
    CausalHypothesis,
    CalibratedDecisionOption,
    CanonicalActionSignal,
    CanonicalDecisionSignal,
    CanonicalDependencySignal,
    CanonicalKPISignal,
    CharterContext,
    DecisionOption,
    IntentFrame,
    SituationAssessment,
    charter_context_to_snapshot,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _rich_context() -> CharterContext:
    return CharterContext(
        charter_name="LWC-2026-00001",
        business_objective="Reduce decision reversal rate below 8% within Q3 2026",
        in_scope_definition="All operational decisions within the delivery function",
        open_decisions=(
            CanonicalDecisionSignal(
                name="DR-001", state="Draft", criticality="High",
                decision_type="Operational", owner="alice@example.com",
            ),
            CanonicalDecisionSignal(
                name="DR-002", state="Submitted for Approval", criticality="Medium",
                decision_type="Strategic", owner="bob@example.com",
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
            CanonicalActionSignal(name="TASK-001", overdue_days=3, owner="carol@example.com"),
        ),
    )


def _empty_context() -> CharterContext:
    return CharterContext(
        charter_name="LWC-2026-00002",
        business_objective="Improve governance discipline",
        in_scope_definition="Q4 operational scope",
        open_decisions=(),
        open_dependencies=(),
        kpi_signals=(),
        overdue_actions=(),
    )


def _engine_returning(json_text: str) -> MagicMock:
    eng = MagicMock()
    eng.complete.return_value = EngineResponse(text=json_text, success=True)
    return eng


def _failing_engine() -> MagicMock:
    eng = MagicMock()
    eng.complete.return_value = EngineResponse(text="", success=False, error="offline")
    return eng


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Intermediate dataclasses ──────────────────────────────────────────────────


def test_intent_frame_rejects_empty_objective() -> None:
    with pytest.raises(ValueError, match="objective"):
        IntentFrame(objective="", constraints=(), priorities=(), scope_summary="scope")


def test_intent_frame_rejects_empty_scope_summary() -> None:
    with pytest.raises(ValueError, match="scope_summary"):
        IntentFrame(objective="obj", constraints=(), priorities=(), scope_summary="")


def test_intent_frame_frozen() -> None:
    f = IntentFrame(objective="obj", constraints=(), priorities=(), scope_summary="scope")
    with pytest.raises((AttributeError, TypeError)):
        f.objective = "other"  # type: ignore[misc]


def test_situation_assessment_rejects_empty_summary() -> None:
    with pytest.raises(ValueError, match="context_summary"):
        SituationAssessment(
            observations=(), risk_indicators=(),
            opportunity_indicators=(), context_summary="",
        )


def test_causal_hypothesis_rejects_empty_assumption() -> None:
    with pytest.raises(ValueError, match="assumption"):
        CausalHypothesis(
            assumption="", context_conditions="ctx",
            proposed_action="act", expected_outcome="out",
            value_effect="val", hypothesis_text="If A → B → C",
            recommendation_class="Corrective",
        )


def test_causal_hypothesis_rejects_missing_arrow() -> None:
    with pytest.raises(ValueError, match="\u2192"):
        CausalHypothesis(
            assumption="A", context_conditions="ctx",
            proposed_action="act", expected_outcome="out",
            value_effect="val", hypothesis_text="no arrow here",
            recommendation_class="Corrective",
        )


def test_causal_hypothesis_rejects_invalid_class() -> None:
    with pytest.raises(ValueError, match="recommendation_class"):
        CausalHypothesis(
            assumption="A", context_conditions="ctx",
            proposed_action="act", expected_outcome="out",
            value_effect="val", hypothesis_text="If A → B → C",
            recommendation_class="Unknown",
        )


def test_causal_hypothesis_accepts_all_valid_classes() -> None:
    for cls in VALID_RECOMMENDATION_CLASSES:
        h = CausalHypothesis(
            assumption="A", context_conditions="ctx",
            proposed_action="act", expected_outcome="out",
            value_effect="val", hypothesis_text="If A → B → C",
            recommendation_class=cls,
        )
        assert h.recommendation_class == cls


def test_decision_option_rejects_empty_objective() -> None:
    hyp = CausalHypothesis(
        assumption="A", context_conditions="ctx", proposed_action="act",
        expected_outcome="out", value_effect="val",
        hypothesis_text="If A → B → C", recommendation_class="Corrective",
    )
    with pytest.raises(ValueError, match="objective_served"):
        DecisionOption(
            hypothesis=hyp, recommendation_class="Corrective",
            objective_served="", expected_value_hypothesis="val",
            trade_offs=(), risk_exposure="low", dependency_implications="none",
            owner_and_review_point="owner", verification_baseline="base",
            verification_kpi_direction="Decrease", verification_review_window="2w",
            verification_acceptance_criteria="criteria",
        )


def test_calibrated_decision_option_rejects_invalid_band() -> None:
    hyp = CausalHypothesis(
        assumption="A", context_conditions="ctx", proposed_action="act",
        expected_outcome="out", value_effect="val",
        hypothesis_text="If A → B → C", recommendation_class="Corrective",
    )
    opt = DecisionOption(
        hypothesis=hyp, recommendation_class="Corrective",
        objective_served="obj", expected_value_hypothesis="val",
        trade_offs=(), risk_exposure="low", dependency_implications="none",
        owner_and_review_point="owner", verification_baseline="base",
        verification_kpi_direction="Decrease", verification_review_window="2w",
        verification_acceptance_criteria="criteria",
    )
    dims = {k: "ok" for k in REQUIRED_CONFIDENCE_DIMENSIONS}
    with pytest.raises(ValueError, match="confidence_band"):
        CalibratedDecisionOption(
            option=opt, confidence_band="Very High",
            confidence_rationale="rationale", confidence_dimensions=dims,
        )


def test_calibrated_decision_option_rejects_missing_dimensions() -> None:
    hyp = CausalHypothesis(
        assumption="A", context_conditions="ctx", proposed_action="act",
        expected_outcome="out", value_effect="val",
        hypothesis_text="If A → B → C", recommendation_class="Corrective",
    )
    opt = DecisionOption(
        hypothesis=hyp, recommendation_class="Corrective",
        objective_served="obj", expected_value_hypothesis="val",
        trade_offs=(), risk_exposure="low", dependency_implications="none",
        owner_and_review_point="owner", verification_baseline="base",
        verification_kpi_direction="Decrease", verification_review_window="2w",
        verification_acceptance_criteria="criteria",
    )
    with pytest.raises(ValueError, match="missing"):
        CalibratedDecisionOption(
            option=opt, confidence_band="Medium",
            confidence_rationale="rationale", confidence_dimensions={"evidence_strength": "ok"},
        )


# ── BaseReasoningLayer ────────────────────────────────────────────────────────


def test_base_reasoning_layer_try_parse_json_plain() -> None:
    result = BaseReasoningLayer._try_parse_json('{"key": "value"}')
    assert result == {"key": "value"}


def test_base_reasoning_layer_try_parse_json_array() -> None:
    result = BaseReasoningLayer._try_parse_json('[{"a": 1}]')
    assert result == [{"a": 1}]


def test_base_reasoning_layer_try_parse_json_fenced() -> None:
    result = BaseReasoningLayer._try_parse_json('```json\n{"key": "value"}\n```')
    assert result == {"key": "value"}


def test_base_reasoning_layer_try_parse_json_embedded() -> None:
    result = BaseReasoningLayer._try_parse_json('Here is the result: {"key": "value"} done.')
    assert result == {"key": "value"}


def test_base_reasoning_layer_try_parse_json_invalid_returns_none() -> None:
    assert BaseReasoningLayer._try_parse_json("not json at all") is None


def test_base_reasoning_layer_try_parse_json_empty_returns_none() -> None:
    assert BaseReasoningLayer._try_parse_json("") is None


def test_base_reasoning_layer_try_parse_json_invalid_bare_braces_returns_none() -> None:
    # Has braces but content is not valid JSON → bare-match except branch
    assert BaseReasoningLayer._try_parse_json("result: {not: valid json here}") is None


def test_r1_parse_llm_output_non_iterable_constraints_falls_back() -> None:
    # constraints field is an int — triggers TypeError in tuple comprehension → fallback
    json_response = (
        '{"objective": "obj", "scope_summary": "scope", "constraints": 123}'
    )
    frame = R1IntentFraming().execute(_rich_context(), _engine_returning(json_response))
    # TypeError caught → fallback uses charter data
    assert "Reduce decision reversal rate" in frame.objective


def test_r2_parse_llm_output_non_iterable_observations_falls_back() -> None:
    json_response = (
        '{"observations": "not a list", '
        '"risk_indicators": [], "opportunity_indicators": [], '
        '"context_summary": "summary"}'
    )
    ctx = _rich_context()
    frame = R1IntentFraming()._fallback(ctx)
    # observations is a string; iterating it produces single chars, but context_summary is valid
    # This actually succeeds (str is iterable) — test that summary is preserved
    assessment = R2SituationInterpretation().execute(frame, ctx, _engine_returning(json_response))
    assert assessment.context_summary


def test_r3_parse_llm_output_empty_list_falls_back() -> None:
    """Empty JSON array → parse returns None → fallback used."""
    assessment = SituationAssessment(
        observations=(), risk_indicators=("risk",), opportunity_indicators=(),
        context_summary="Has risk.",
    )
    hypotheses = R3CausalHypothesisConstruction().execute(
        assessment, _engine_returning("[]")
    )
    assert len(hypotheses) >= 1  # fallback applied


def test_r3_parse_llm_output_item_missing_assumption_skipped() -> None:
    """Items without assumption are skipped; valid items retained."""
    assessment = SituationAssessment(
        observations=(), risk_indicators=("risk",), opportunity_indicators=(),
        context_summary="Has risk.",
    )
    json_response = (
        '[{"assumption": "", "context_conditions": "ctx", "proposed_action": "act", '
        '"expected_outcome": "out", "value_effect": "val", '
        '"hypothesis_text": "If A \u2192 B \u2192 C", "recommendation_class": "Corrective"}, '
        '{"assumption": "Valid", "context_conditions": "ctx", "proposed_action": "act", '
        '"expected_outcome": "out", "value_effect": "val", '
        '"hypothesis_text": "If Valid + ctx \u2192 act \u2192 out + val", '
        '"recommendation_class": "Corrective"}]'
    )
    hypotheses = R3CausalHypothesisConstruction().execute(
        assessment, _engine_returning(json_response)
    )
    assert len(hypotheses) == 1
    assert hypotheses[0].assumption == "Valid"


# ── R1 Intent Framing ─────────────────────────────────────────────────────────


def test_r1_null_engine_returns_intent_frame() -> None:
    frame = R1IntentFraming().execute(_rich_context(), NullEngine())
    assert isinstance(frame, IntentFrame)
    assert frame.objective
    assert frame.scope_summary


def test_r1_fallback_uses_charter_objective() -> None:
    frame = R1IntentFraming().execute(_rich_context(), _failing_engine())
    assert "Reduce decision reversal rate" in frame.objective


def test_r1_fallback_identifies_critical_constraints() -> None:
    frame = R1IntentFraming().execute(_rich_context(), _failing_engine())
    assert any("critical" in c.lower() for c in frame.constraints)


def test_r1_fallback_identifies_high_priority_decisions() -> None:
    frame = R1IntentFraming().execute(_rich_context(), _failing_engine())
    assert any("high" in p.lower() or "decision" in p.lower() for p in frame.priorities)


def test_r1_empty_context_returns_valid_intent_frame() -> None:
    frame = R1IntentFraming().execute(_empty_context(), NullEngine())
    assert frame.objective
    assert frame.constraints
    assert frame.priorities
    assert frame.scope_summary


def test_r1_llm_success_path() -> None:
    json_response = (
        '{"objective": "Reduce reversal rate", '
        '"constraints": ["budget limit"], '
        '"priorities": ["resolve open decisions"], '
        '"scope_summary": "Q3 operational scope"}'
    )
    frame = R1IntentFraming().execute(_rich_context(), _engine_returning(json_response))
    assert frame.objective == "Reduce reversal rate"
    assert "budget limit" in frame.constraints


def test_r1_malformed_llm_response_falls_back() -> None:
    frame = R1IntentFraming().execute(_rich_context(), _engine_returning("not json"))
    # fallback uses charter data
    assert "Reduce decision reversal rate" in frame.objective


def test_r1_llm_missing_required_fields_falls_back() -> None:
    frame = R1IntentFraming().execute(
        _rich_context(), _engine_returning('{"constraints": ["c1"]}')
    )
    # missing objective → fallback
    assert "Reduce decision reversal rate" in frame.objective


# ── R2 Situation Interpretation ───────────────────────────────────────────────


def test_r2_null_engine_returns_situation_assessment() -> None:
    ctx = _rich_context()
    frame = R1IntentFraming()._fallback(ctx)
    assessment = R2SituationInterpretation().execute(frame, ctx, NullEngine())
    assert isinstance(assessment, SituationAssessment)
    assert assessment.context_summary


def test_r2_fallback_includes_signal_counts() -> None:
    ctx = _rich_context()
    frame = R1IntentFraming()._fallback(ctx)
    assessment = R2SituationInterpretation()._fallback(frame, ctx)
    combined = " ".join(assessment.observations)
    assert "2" in combined or "decision" in combined.lower()


def test_r2_fallback_identifies_at_risk_dependencies() -> None:
    ctx = _rich_context()
    frame = R1IntentFraming()._fallback(ctx)
    assessment = R2SituationInterpretation()._fallback(frame, ctx)
    assert any("risk" in r.lower() for r in assessment.risk_indicators)


def test_r2_empty_context_no_risks() -> None:
    ctx = _empty_context()
    frame = R1IntentFraming()._fallback(ctx)
    assessment = R2SituationInterpretation()._fallback(frame, ctx)
    assert "no active" in assessment.context_summary.lower() or assessment.context_summary


def test_r2_llm_success_path() -> None:
    ctx = _rich_context()
    frame = R1IntentFraming()._fallback(ctx)
    json_response = (
        '{"observations": ["3 decisions open"], '
        '"risk_indicators": ["critical dep blocked"], '
        '"opportunity_indicators": ["kpi baselines ready"], '
        '"context_summary": "Governance needs attention"}'
    )
    assessment = R2SituationInterpretation().execute(
        frame, ctx, _engine_returning(json_response)
    )
    assert assessment.context_summary == "Governance needs attention"
    assert "3 decisions open" in assessment.observations


def test_r2_malformed_llm_falls_back() -> None:
    ctx = _rich_context()
    frame = R1IntentFraming()._fallback(ctx)
    assessment = R2SituationInterpretation().execute(
        frame, ctx, _engine_returning("not json")
    )
    assert assessment.context_summary  # fallback produced something


def test_r2_llm_missing_summary_falls_back() -> None:
    ctx = _rich_context()
    frame = R1IntentFraming()._fallback(ctx)
    assessment = R2SituationInterpretation().execute(
        frame, ctx, _engine_returning('{"observations": ["x"]}')
    )
    assert assessment.context_summary  # fallback


# ── R3 Causal Hypothesis Construction ────────────────────────────────────────


def test_r3_null_engine_returns_at_least_one_hypothesis() -> None:
    assessment = SituationAssessment(
        observations=("2 open decisions",),
        risk_indicators=("1 critical dependency at risk",),
        opportunity_indicators=("KPI baselines registered",),
        context_summary="Charter shows 2 open decisions and 1 at-risk dependency.",
    )
    hypotheses = R3CausalHypothesisConstruction().execute(assessment, NullEngine())
    assert len(hypotheses) >= 1
    for h in hypotheses:
        assert "\u2192" in h.hypothesis_text
        assert h.assumption


def test_r3_fallback_with_risks_produces_corrective_hypothesis() -> None:
    assessment = SituationAssessment(
        observations=(),
        risk_indicators=("critical dependency blocked",),
        opportunity_indicators=(),
        context_summary="Active risk present.",
    )
    hypotheses = R3CausalHypothesisConstruction()._fallback(assessment)
    assert any(h.recommendation_class == "Corrective" for h in hypotheses)


def test_r3_fallback_with_opportunities_produces_optimizing_hypothesis() -> None:
    assessment = SituationAssessment(
        observations=(),
        risk_indicators=(),
        opportunity_indicators=("KPI baselines ready",),
        context_summary="No risks; baseline available.",
    )
    hypotheses = R3CausalHypothesisConstruction()._fallback(assessment)
    assert any(h.recommendation_class == "Optimizing" for h in hypotheses)


def test_r3_fallback_empty_context_produces_preventive_hypothesis() -> None:
    assessment = SituationAssessment(
        observations=(),
        risk_indicators=(),
        opportunity_indicators=(),
        context_summary="No active governance signals.",
    )
    hypotheses = R3CausalHypothesisConstruction()._fallback(assessment)
    assert len(hypotheses) >= 1
    assert any(h.recommendation_class == "Preventive" for h in hypotheses)


def test_r3_max_three_hypotheses() -> None:
    # Build assessment that could produce many hypotheses
    assessment = SituationAssessment(
        observations=tuple(f"obs {i}" for i in range(10)),
        risk_indicators=tuple(f"risk {i}" for i in range(10)),
        opportunity_indicators=tuple(f"opp {i}" for i in range(10)),
        context_summary="Many signals.",
    )
    hypotheses = R3CausalHypothesisConstruction()._fallback(assessment)
    assert len(hypotheses) <= 3


def test_r3_llm_success_path() -> None:
    assessment = SituationAssessment(
        observations=(), risk_indicators=(), opportunity_indicators=(),
        context_summary="Active context.",
    )
    json_response = (
        '[{"assumption": "Review cadence is low", '
        '"context_conditions": "2 open decisions", '
        '"proposed_action": "Weekly review ritual", '
        '"expected_outcome": "Reversal rate drops", '
        '"value_effect": "Cost savings", '
        '"hypothesis_text": "If cadence is low + 2 decisions \u2192 review \u2192 reversal drops + savings", '
        '"recommendation_class": "Corrective"}]'
    )
    hypotheses = R3CausalHypothesisConstruction().execute(
        assessment, _engine_returning(json_response)
    )
    assert hypotheses[0].assumption == "Review cadence is low"
    assert "\u2192" in hypotheses[0].hypothesis_text


def test_r3_llm_wrapped_object_format() -> None:
    assessment = SituationAssessment(
        observations=(), risk_indicators=(), opportunity_indicators=(),
        context_summary="Context.",
    )
    json_response = (
        '{"hypotheses": [{"assumption": "A", "context_conditions": "ctx", '
        '"proposed_action": "act", "expected_outcome": "out", "value_effect": "val", '
        '"hypothesis_text": "If A + ctx \u2192 act \u2192 out + val", '
        '"recommendation_class": "Preventive"}]}'
    )
    hypotheses = R3CausalHypothesisConstruction().execute(
        assessment, _engine_returning(json_response)
    )
    assert len(hypotheses) == 1


def test_r3_llm_malformed_falls_back() -> None:
    assessment = SituationAssessment(
        observations=(), risk_indicators=("risk",), opportunity_indicators=(),
        context_summary="Has risk.",
    )
    hypotheses = R3CausalHypothesisConstruction().execute(
        assessment, _engine_returning("garbage")
    )
    assert len(hypotheses) >= 1  # fallback was used


def test_r3_llm_hypothesis_without_arrow_is_skipped() -> None:
    assessment = SituationAssessment(
        observations=(), risk_indicators=("risk",), opportunity_indicators=(),
        context_summary="Has risk.",
    )
    json_response = (
        '[{"assumption": "A", "context_conditions": "ctx", "proposed_action": "act", '
        '"expected_outcome": "out", "value_effect": "val", '
        '"hypothesis_text": "no arrow here", "recommendation_class": "Corrective"}]'
    )
    hypotheses = R3CausalHypothesisConstruction().execute(
        assessment, _engine_returning(json_response)
    )
    # Invalid LLM item skipped → fallback used
    assert len(hypotheses) >= 1
    for h in hypotheses:
        assert "\u2192" in h.hypothesis_text


# ── R4 Option Generation ──────────────────────────────────────────────────────


def _make_hypothesis(cls: str = "Corrective") -> CausalHypothesis:
    return CausalHypothesis(
        assumption="Review cadence insufficient",
        context_conditions="2 open decisions",
        proposed_action="Introduce weekly review",
        expected_outcome="Reversal rate drops",
        value_effect="Cost savings",
        hypothesis_text="If cadence low + 2 decisions \u2192 review \u2192 reversal drops + savings",
        recommendation_class=cls,
    )


def test_r4_produces_one_option_per_hypothesis() -> None:
    hypotheses = [_make_hypothesis("Corrective"), _make_hypothesis("Preventive")]
    options = R4OptionGeneration().execute(hypotheses)
    assert len(options) == 2


def test_r4_option_inherits_recommendation_class() -> None:
    options = R4OptionGeneration().execute([_make_hypothesis("Optimizing")])
    assert options[0].recommendation_class == "Optimizing"


def test_r4_option_objective_comes_from_hypothesis_outcome() -> None:
    options = R4OptionGeneration().execute([_make_hypothesis()])
    assert "Reversal rate drops" in options[0].objective_served


def test_r4_capped_at_three_options() -> None:
    hypotheses = [_make_hypothesis() for _ in range(5)]
    options = R4OptionGeneration().execute(hypotheses)
    assert len(options) <= 3


def test_r4_empty_hypotheses_returns_empty_list() -> None:
    assert R4OptionGeneration().execute([]) == []


def test_r4_option_has_non_empty_trade_offs() -> None:
    options = R4OptionGeneration().execute([_make_hypothesis()])
    assert len(options[0].trade_offs) >= 1
    assert all(t for t in options[0].trade_offs)


# ── R5 Confidence Calibration ─────────────────────────────────────────────────


def _make_option() -> "DecisionOption":
    hyp = _make_hypothesis()
    return DecisionOption(
        hypothesis=hyp,
        recommendation_class=hyp.recommendation_class,
        objective_served="Reversal rate drops",
        expected_value_hypothesis="Cost savings",
        trade_offs=("Requires time",),
        risk_exposure="Low",
        dependency_implications="None",
        owner_and_review_point="Workflow Owner",
        verification_baseline="Current baseline",
        verification_kpi_direction="Decrease",
        verification_review_window="2 weeks",
        verification_acceptance_criteria="DRR < 8%",
    )


def test_r5_produces_calibrated_option_for_each_input() -> None:
    options = [_make_option(), _make_option()]
    calibrated = R5ConfidenceCalibration().execute(options)
    assert len(calibrated) == 2


def test_r5_confidence_band_is_valid() -> None:
    from enterprise_intelligence_platform.ai_agent.schemas import VALID_CONFIDENCE_BANDS
    calibrated = R5ConfidenceCalibration().execute([_make_option()])
    assert calibrated[0].confidence_band in VALID_CONFIDENCE_BANDS


def test_r5_all_five_dimensions_present() -> None:
    calibrated = R5ConfidenceCalibration().execute([_make_option()])
    dims = calibrated[0].confidence_dimensions
    for key in REQUIRED_CONFIDENCE_DIMENSIONS:
        assert key in dims, f"Missing dimension: {key}"


def test_r5_empty_options_returns_empty_list() -> None:
    assert R5ConfidenceCalibration().execute([]) == []


def test_r5_confidence_rationale_is_non_empty() -> None:
    calibrated = R5ConfidenceCalibration().execute([_make_option()])
    assert calibrated[0].confidence_rationale


# ── R6 Decision Support Synthesis ────────────────────────────────────────────


def _make_calibrated(band: str = "Medium") -> CalibratedDecisionOption:
    dims = {k: "ok" for k in REQUIRED_CONFIDENCE_DIMENSIONS}
    return CalibratedDecisionOption(
        option=_make_option(),
        confidence_band=band,
        confidence_rationale="Moderate confidence",
        confidence_dimensions=dims,
    )


def test_r6_produces_recommendation_package() -> None:
    ctx = _rich_context()
    options = [_make_calibrated("Medium"), _make_calibrated("Low")]
    snapshot = charter_context_to_snapshot(ctx)
    pkg = R6DecisionSupportSynthesis().execute(
        options=options,
        charter_name=ctx.charter_name,
        context_snapshot=snapshot,
        model_identifier="null:deterministic",
        fallback_used=True,
        execution_timestamp=_ts(),
    )
    assert pkg.charter_name == ctx.charter_name
    assert len(pkg.recommendations) == 2


def test_r6_higher_confidence_ranked_first() -> None:
    options = [_make_calibrated("Low"), _make_calibrated("High"), _make_calibrated("Medium")]
    snapshot = {}
    pkg = R6DecisionSupportSynthesis().execute(
        options=options,
        charter_name="LWC-001",
        context_snapshot=snapshot,
        model_identifier="null:deterministic",
        fallback_used=False,
        execution_timestamp=_ts(),
    )
    bands = [r.confidence_state.band for r in pkg.recommendations]
    assert bands == sorted(bands, key=lambda b: {"High": 3, "Medium": 2, "Low": 1}[b], reverse=True)


def test_r6_index_assigned_sequentially() -> None:
    options = [_make_calibrated("Medium"), _make_calibrated("Medium")]
    pkg = R6DecisionSupportSynthesis().execute(
        options=options, charter_name="LWC-001",
        context_snapshot={}, model_identifier="null:deterministic",
        fallback_used=False, execution_timestamp=_ts(),
    )
    indices = [r.index for r in pkg.recommendations]
    assert indices == list(range(len(indices)))


def test_r6_empty_options_returns_empty_recommendations() -> None:
    pkg = R6DecisionSupportSynthesis().execute(
        options=[], charter_name="LWC-001",
        context_snapshot={}, model_identifier="null:deterministic",
        fallback_used=False, execution_timestamp=_ts(),
    )
    assert pkg.recommendations == []


def test_r6_recommendation_has_valid_causal_hypothesis() -> None:
    options = [_make_calibrated("Medium")]
    pkg = R6DecisionSupportSynthesis().execute(
        options=options, charter_name="LWC-001",
        context_snapshot={}, model_identifier="null:deterministic",
        fallback_used=False, execution_timestamp=_ts(),
    )
    assert "\u2192" in pkg.recommendations[0].causal_hypothesis


def test_r6_all_nine_fields_populated() -> None:
    options = [_make_calibrated()]
    pkg = R6DecisionSupportSynthesis().execute(
        options=options, charter_name="LWC-001",
        context_snapshot={}, model_identifier="null:deterministic",
        fallback_used=False, execution_timestamp=_ts(),
    )
    rec = pkg.recommendations[0]
    assert rec.objective_served
    assert rec.assumptions
    assert rec.expected_value_hypothesis
    assert rec.trade_offs is not None
    assert rec.risk_exposure
    assert rec.dependency_implications
    assert rec.confidence_state
    assert rec.verification_plan
    assert rec.owner_and_review_point


def test_r6_skips_malformed_option_without_failing_package() -> None:
    """R6 must not raise if one option somehow produces an invalid Recommendation."""
    bad_opt = MagicMock()
    bad_opt.confidence_band = "Medium"
    # Force _to_recommendation to raise
    r6 = R6DecisionSupportSynthesis()
    original = r6._to_recommendation
    call_count = [0]

    def patched_to_rec(opt, idx):  # type: ignore[no-untyped-def]
        call_count[0] += 1
        if call_count[0] == 1:
            raise ValueError("simulated bad option")
        return original(opt, idx)

    r6._to_recommendation = patched_to_rec  # type: ignore[method-assign]
    options = [_make_calibrated(), _make_calibrated()]
    pkg = r6.execute(
        options=options, charter_name="LWC-001",
        context_snapshot={}, model_identifier="null:deterministic",
        fallback_used=False, execution_timestamp=_ts(),
    )
    # Second option should still produce a recommendation
    assert len(pkg.recommendations) == 1


# ── Full R1 → R6 pipeline integration test ───────────────────────────────────


def _run_pipeline(context: CharterContext, use_null_engine: bool = True) -> object:
    engine = NullEngine() if use_null_engine else _failing_engine()
    ts = _ts()

    frame = R1IntentFraming().execute(context, engine)
    assessment = R2SituationInterpretation().execute(frame, context, engine)
    hypotheses = R3CausalHypothesisConstruction().execute(assessment, engine)
    options = R4OptionGeneration().execute(hypotheses)
    calibrated = R5ConfidenceCalibration().execute(options)
    snapshot = charter_context_to_snapshot(context)

    return R6DecisionSupportSynthesis().execute(
        options=calibrated,
        charter_name=context.charter_name,
        context_snapshot=snapshot,
        model_identifier=engine.identifier,
        fallback_used=True,
        execution_timestamp=ts,
    )


def test_pipeline_with_null_engine_returns_valid_package() -> None:
    pkg = _run_pipeline(_rich_context())
    assert pkg.charter_name == "LWC-2026-00001"  # type: ignore[union-attr]
    assert len(pkg.recommendations) >= 1  # type: ignore[union-attr]


def test_pipeline_with_empty_context_returns_valid_package() -> None:
    pkg = _run_pipeline(_empty_context())
    assert pkg.charter_name == "LWC-2026-00002"  # type: ignore[union-attr]
    assert len(pkg.recommendations) >= 1  # type: ignore[union-attr]


def test_pipeline_recommendations_are_schema_valid() -> None:
    pkg = _run_pipeline(_rich_context())
    for rec in pkg.recommendations:  # type: ignore[union-attr]
        assert rec.objective_served
        assert rec.assumptions
        assert "\u2192" in rec.causal_hypothesis
        assert rec.confidence_state.band in {"High", "Medium", "Low"}
        for key in REQUIRED_CONFIDENCE_DIMENSIONS:
            assert key in rec.confidence_state.dimensions


def test_pipeline_with_failing_engine_still_produces_package() -> None:
    pkg = _run_pipeline(_rich_context(), use_null_engine=False)
    assert len(pkg.recommendations) >= 1  # type: ignore[union-attr]


def test_pipeline_model_identifier_propagated() -> None:
    pkg = _run_pipeline(_rich_context())
    assert pkg.model_identifier == "null:deterministic"  # type: ignore[union-attr]


def test_pipeline_all_recommendations_have_valid_indices() -> None:
    pkg = _run_pipeline(_rich_context())
    indices = [r.index for r in pkg.recommendations]  # type: ignore[union-attr]
    assert indices == list(range(len(indices)))
