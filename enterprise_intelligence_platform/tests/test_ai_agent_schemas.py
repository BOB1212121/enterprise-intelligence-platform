"""Tests for ai_agent/schemas.py.

Pure-Python tests — no Frappe initialisation required.
Run with:  python -m pytest enterprise_intelligence_platform/tests/test_ai_agent_schemas.py -v
"""
import json

import pytest

from enterprise_intelligence_platform.ai_agent.schemas import (
    REQUIRED_CONFIDENCE_DIMENSIONS,
    VALID_CONFIDENCE_BANDS,
    VALID_RECOMMENDATION_CLASSES,
    CanonicalActionSignal,
    CanonicalDecisionSignal,
    CanonicalDependencySignal,
    CanonicalKPISignal,
    CharterContext,
    ConfidenceState,
    Recommendation,
    RecommendationPackage,
    VerificationPlan,
    charter_context_to_snapshot,
    recommendation_from_dict,
    recommendation_to_dict,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _valid_dimensions() -> dict[str, str]:
    return {k: "adequate" for k in REQUIRED_CONFIDENCE_DIMENSIONS}


def _valid_confidence() -> ConfidenceState:
    return ConfidenceState(band="Medium", rationale="adequate evidence", dimensions=_valid_dimensions())


def _valid_plan() -> VerificationPlan:
    return VerificationPlan(
        baseline="current DRR = 12%",
        expected_kpi_direction="Decrease",
        review_window="2 weeks",
        acceptance_criteria="DRR drops below 8%",
    )


def _valid_recommendation(index: int = 0) -> Recommendation:
    return Recommendation(
        index=index,
        recommendation_class="Corrective",
        objective_served="Reduce decision reversal rate",
        assumptions=["Current DRR is above acceptable threshold"],
        expected_value_hypothesis="Structured review will reduce reversals by 30%",
        trade_offs=["Requires 2-hour weekly review session"],
        risk_exposure="Medium — team may resist additional cadence",
        dependency_implications="None — no external dependencies",
        confidence_state=_valid_confidence(),
        verification_plan=_valid_plan(),
        owner_and_review_point="EIP Workflow Owner — review after 2-week window",
        causal_hypothesis=(
            "If DRR > 10% + no structured review ritual "
            "→ introduce weekly decision review "
            "→ DRR decreases + reduction in rework cost"
        ),
    )


def _valid_charter_context() -> CharterContext:
    return CharterContext(
        charter_name="LWC-2026-00001",
        business_objective="Reduce decision reversal rate below 8%",
        in_scope_definition="All operational decisions within Q3 2026",
        open_decisions=(
            CanonicalDecisionSignal(
                name="DR-001", state="Draft", criticality="High",
                decision_type="Operational", owner="admin@example.com",
            ),
        ),
        open_dependencies=(
            CanonicalDependencySignal(
                name="DER-001", criticality="Critical", status="At Risk",
                dependency_type="System", days_overdue=3,
            ),
        ),
        kpi_signals=(
            CanonicalKPISignal(kpi_code="DRR", baseline_value=12.0, data_source="ERP"),
        ),
        overdue_actions=(
            CanonicalActionSignal(name="TASK-001", overdue_days=5, owner="admin@example.com"),
        ),
    )


# ── CanonicalDecisionSignal ───────────────────────────────────────────────────


def test_canonical_decision_signal_construction() -> None:
    sig = CanonicalDecisionSignal(
        name="DR-001", state="Draft", criticality="High",
        decision_type="Operational", owner="user@example.com",
    )
    assert sig.name == "DR-001"
    assert sig.criticality == "High"


def test_canonical_decision_signal_is_frozen() -> None:
    sig = CanonicalDecisionSignal(
        name="DR-001", state="Draft", criticality="High",
        decision_type="Operational", owner="user@example.com",
    )
    with pytest.raises((AttributeError, TypeError)):
        sig.name = "DR-002"  # type: ignore[misc]


# ── CanonicalDependencySignal ─────────────────────────────────────────────────


def test_canonical_dependency_signal_construction() -> None:
    sig = CanonicalDependencySignal(
        name="DER-001", criticality="Critical", status="At Risk",
        dependency_type="System", days_overdue=5,
    )
    assert sig.days_overdue == 5
    assert sig.status == "At Risk"


# ── CanonicalKPISignal ────────────────────────────────────────────────────────


def test_canonical_kpi_signal_construction() -> None:
    sig = CanonicalKPISignal(kpi_code="DRR", baseline_value=12.5, data_source="ERP")
    assert sig.kpi_code == "DRR"
    assert sig.baseline_value == 12.5


# ── CanonicalActionSignal ─────────────────────────────────────────────────────


def test_canonical_action_signal_construction() -> None:
    sig = CanonicalActionSignal(name="TASK-001", overdue_days=3, owner="user@example.com")
    assert sig.overdue_days == 3


# ── CharterContext ────────────────────────────────────────────────────────────


def test_charter_context_valid_construction() -> None:
    ctx = _valid_charter_context()
    assert ctx.charter_name == "LWC-2026-00001"
    assert len(ctx.open_decisions) == 1
    assert len(ctx.kpi_signals) == 1


def test_charter_context_rejects_empty_charter_name() -> None:
    with pytest.raises(ValueError, match="charter_name"):
        CharterContext(
            charter_name="",
            business_objective="Obj",
            in_scope_definition="Scope",
            open_decisions=(),
            open_dependencies=(),
            kpi_signals=(),
            overdue_actions=(),
        )


def test_charter_context_rejects_empty_business_objective() -> None:
    with pytest.raises(ValueError, match="business_objective"):
        CharterContext(
            charter_name="LWC-001",
            business_objective="",
            in_scope_definition="Scope",
            open_decisions=(),
            open_dependencies=(),
            kpi_signals=(),
            overdue_actions=(),
        )


def test_charter_context_accepts_empty_signal_collections() -> None:
    ctx = CharterContext(
        charter_name="LWC-001",
        business_objective="Objective",
        in_scope_definition="Scope",
        open_decisions=(),
        open_dependencies=(),
        kpi_signals=(),
        overdue_actions=(),
    )
    assert ctx.open_decisions == ()
    assert ctx.overdue_actions == ()


def test_charter_context_is_frozen() -> None:
    ctx = _valid_charter_context()
    with pytest.raises((AttributeError, TypeError)):
        ctx.charter_name = "other"  # type: ignore[misc]


# ── ConfidenceState ───────────────────────────────────────────────────────────


def test_confidence_state_valid_construction() -> None:
    cs = _valid_confidence()
    assert cs.band == "Medium"
    assert len(cs.dimensions) == 5


def test_confidence_state_rejects_invalid_band() -> None:
    with pytest.raises(ValueError, match="confidence band"):
        ConfidenceState(band="Very High", rationale="ok", dimensions=_valid_dimensions())


def test_confidence_state_rejects_empty_rationale() -> None:
    with pytest.raises(ValueError, match="rationale"):
        ConfidenceState(band="High", rationale="", dimensions=_valid_dimensions())


def test_confidence_state_rejects_missing_dimensions() -> None:
    dims = _valid_dimensions()
    del dims["freshness"]
    with pytest.raises(ValueError, match="freshness"):
        ConfidenceState(band="Low", rationale="ok", dimensions=dims)


def test_confidence_state_accepts_all_valid_bands() -> None:
    for band in VALID_CONFIDENCE_BANDS:
        cs = ConfidenceState(band=band, rationale="test", dimensions=_valid_dimensions())
        assert cs.band == band


# ── VerificationPlan ──────────────────────────────────────────────────────────


def test_verification_plan_valid_construction() -> None:
    vp = _valid_plan()
    assert vp.expected_kpi_direction == "Decrease"
    assert vp.review_window == "2 weeks"


def test_verification_plan_is_frozen() -> None:
    vp = _valid_plan()
    with pytest.raises((AttributeError, TypeError)):
        vp.baseline = "other"  # type: ignore[misc]


# ── Recommendation ────────────────────────────────────────────────────────────


def test_recommendation_valid_construction() -> None:
    rec = _valid_recommendation()
    assert rec.index == 0
    assert len(rec.assumptions) == 1
    assert "→" in rec.causal_hypothesis


def test_recommendation_rejects_empty_assumptions() -> None:
    with pytest.raises(ValueError, match="assumptions"):
        Recommendation(
            index=0,
            recommendation_class="Corrective",
            objective_served="Obj",
            assumptions=[],
            expected_value_hypothesis="Hyp",
            trade_offs=[],
            risk_exposure="Low",
            dependency_implications="None",
            confidence_state=_valid_confidence(),
            verification_plan=_valid_plan(),
            owner_and_review_point="Owner",
            causal_hypothesis="If A → B → C",
        )


def test_recommendation_rejects_blank_assumption_entry() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        Recommendation(
            index=0,
            recommendation_class="Corrective",
            objective_served="Obj",
            assumptions=["valid assumption", "   "],
            expected_value_hypothesis="Hyp",
            trade_offs=[],
            risk_exposure="Low",
            dependency_implications="None",
            confidence_state=_valid_confidence(),
            verification_plan=_valid_plan(),
            owner_and_review_point="Owner",
            causal_hypothesis="If A → B → C",
        )


def test_recommendation_rejects_invalid_class() -> None:
    with pytest.raises(ValueError, match="recommendation_class"):
        Recommendation(
            index=0,
            recommendation_class="Invalid",
            objective_served="Obj",
            assumptions=["A"],
            expected_value_hypothesis="Hyp",
            trade_offs=[],
            risk_exposure="Low",
            dependency_implications="None",
            confidence_state=_valid_confidence(),
            verification_plan=_valid_plan(),
            owner_and_review_point="Owner",
            causal_hypothesis="If A → B → C",
        )


def test_recommendation_rejects_empty_objective() -> None:
    with pytest.raises(ValueError, match="objective_served"):
        Recommendation(
            index=0,
            recommendation_class="Corrective",
            objective_served="",
            assumptions=["A"],
            expected_value_hypothesis="Hyp",
            trade_offs=[],
            risk_exposure="Low",
            dependency_implications="None",
            confidence_state=_valid_confidence(),
            verification_plan=_valid_plan(),
            owner_and_review_point="Owner",
            causal_hypothesis="If A → B → C",
        )


def test_recommendation_rejects_causal_hypothesis_without_arrow() -> None:
    with pytest.raises(ValueError, match="causal arrow"):
        Recommendation(
            index=0,
            recommendation_class="Corrective",
            objective_served="Obj",
            assumptions=["A"],
            expected_value_hypothesis="Hyp",
            trade_offs=[],
            risk_exposure="Low",
            dependency_implications="None",
            confidence_state=_valid_confidence(),
            verification_plan=_valid_plan(),
            owner_and_review_point="Owner",
            causal_hypothesis="No arrow here",
        )


def test_recommendation_accepts_all_valid_classes() -> None:
    for cls in VALID_RECOMMENDATION_CLASSES:
        rec = Recommendation(
            index=0,
            recommendation_class=cls,
            objective_served="Obj",
            assumptions=["A"],
            expected_value_hypothesis="Hyp",
            trade_offs=[],
            risk_exposure="Low",
            dependency_implications="None",
            confidence_state=_valid_confidence(),
            verification_plan=_valid_plan(),
            owner_and_review_point="Owner",
            causal_hypothesis="If A → B → C",
        )
        assert rec.recommendation_class == cls


def test_recommendation_all_nine_fields_accessible() -> None:
    rec = _valid_recommendation()
    # Verify all 9 Phase 6 §10.1 fields are present and non-None
    assert rec.objective_served
    assert rec.assumptions
    assert rec.expected_value_hypothesis
    assert rec.trade_offs is not None  # may be empty list
    assert rec.risk_exposure
    assert rec.dependency_implications
    assert rec.confidence_state
    assert rec.verification_plan
    assert rec.owner_and_review_point


# ── RecommendationPackage ─────────────────────────────────────────────────────


def test_recommendation_package_valid_construction() -> None:
    pkg = RecommendationPackage(
        charter_name="LWC-001",
        recommendations=[_valid_recommendation()],
        context_snapshot={"charter_name": "LWC-001"},
        model_identifier="null:deterministic",
        fallback_used=True,
        execution_timestamp="2026-08-05T10:00:00Z",
    )
    assert pkg.charter_name == "LWC-001"
    assert len(pkg.recommendations) == 1


def test_recommendation_package_rejects_empty_charter_name() -> None:
    with pytest.raises(ValueError, match="charter_name"):
        RecommendationPackage(
            charter_name="",
            recommendations=[],
            context_snapshot={},
            model_identifier="null:deterministic",
            fallback_used=True,
            execution_timestamp="2026-08-05T10:00:00Z",
        )


def test_recommendation_package_rejects_empty_model_identifier() -> None:
    with pytest.raises(ValueError, match="model_identifier"):
        RecommendationPackage(
            charter_name="LWC-001",
            recommendations=[],
            context_snapshot={},
            model_identifier="",
            fallback_used=True,
            execution_timestamp="2026-08-05T10:00:00Z",
        )


def test_recommendation_package_accepts_empty_recommendations() -> None:
    """Empty recommendations are valid — context with no signals produces no recommendations."""
    pkg = RecommendationPackage(
        charter_name="LWC-001",
        recommendations=[],
        context_snapshot={},
        model_identifier="null:deterministic",
        fallback_used=False,
        execution_timestamp="2026-08-05T10:00:00Z",
    )
    assert pkg.recommendations == []


# ── recommendation_to_dict ────────────────────────────────────────────────────


def test_recommendation_to_dict_has_all_required_keys() -> None:
    rec = _valid_recommendation()
    d = recommendation_to_dict(rec)
    required_keys = {
        "index", "recommendation_class", "objective_served", "assumptions",
        "expected_value_hypothesis", "trade_offs", "risk_exposure",
        "dependency_implications", "confidence_state", "verification_plan",
        "owner_and_review_point", "causal_hypothesis",
    }
    assert required_keys.issubset(d.keys())


def test_recommendation_to_dict_is_json_serialisable() -> None:
    rec = _valid_recommendation()
    d = recommendation_to_dict(rec)
    serialised = json.dumps(d)
    assert serialised  # non-empty string
    reparsed = json.loads(serialised)
    assert reparsed["index"] == 0


def test_recommendation_to_dict_confidence_dimensions_present() -> None:
    rec = _valid_recommendation()
    d = recommendation_to_dict(rec)
    dims = d["confidence_state"]["dimensions"]
    for key in REQUIRED_CONFIDENCE_DIMENSIONS:
        assert key in dims


# ── recommendation_package to_api_dict ───────────────────────────────────────


def test_to_api_dict_is_json_serialisable() -> None:
    pkg = RecommendationPackage(
        charter_name="LWC-001",
        recommendations=[_valid_recommendation(0), _valid_recommendation(1)],
        context_snapshot={"charter_name": "LWC-001"},
        model_identifier="null:deterministic",
        fallback_used=False,
        execution_timestamp="2026-08-05T10:00:00Z",
    )
    d = pkg.to_api_dict()
    serialised = json.dumps(d)
    reparsed = json.loads(serialised)
    assert len(reparsed["recommendations"]) == 2


# ── charter_context_to_snapshot ──────────────────────────────────────────────


def test_charter_context_to_snapshot_is_json_serialisable() -> None:
    ctx = _valid_charter_context()
    snapshot = charter_context_to_snapshot(ctx)
    serialised = json.dumps(snapshot)
    reparsed = json.loads(serialised)
    assert reparsed["charter_name"] == "LWC-2026-00001"
    assert len(reparsed["open_decisions"]) == 1
    assert len(reparsed["kpi_signals"]) == 1


def test_charter_context_snapshot_contains_no_erpnext_field_names() -> None:
    """Canonical boundary check: ERPNext DocType field names must not appear in the snapshot."""
    ctx = _valid_charter_context()
    snapshot_str = json.dumps(charter_context_to_snapshot(ctx))
    forbidden = {
        "approval_state", "dependency_status", "lighthouse_workflow_charter",
        "accountable_owner", "executive_sponsor", "naming_series",
    }
    for term in forbidden:
        assert term not in snapshot_str, f"ERPNext field name leaked into snapshot: {term!r}"


# ── recommendation_from_dict round-trip ──────────────────────────────────────


def test_recommendation_from_dict_round_trip() -> None:
    rec = _valid_recommendation()
    d = recommendation_to_dict(rec)
    restored = recommendation_from_dict(d)
    assert restored.index == rec.index
    assert restored.recommendation_class == rec.recommendation_class
    assert restored.assumptions == rec.assumptions
    assert restored.confidence_state.band == rec.confidence_state.band
    assert restored.causal_hypothesis == rec.causal_hypothesis
