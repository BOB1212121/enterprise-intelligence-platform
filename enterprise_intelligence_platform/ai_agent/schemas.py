"""Canonical data contracts for the AI reasoning agent.

All dataclasses here are pure Python — no Frappe imports.
They form the single source of truth for:
  - what the ERPNext context reader may produce (canonical signal types),
  - what the reasoning engine must return (Recommendation, RecommendationPackage),
  - what the service layer persists (trace snapshot helpers).

Governance authority: PHASE_6_AI_REASONING_ARCHITECTURE_MODEL_AGNOSTIC.md §10.1,
REFERENCE_ARCHITECTURE.md §2 (ACL / canonical boundary rule).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ── Sentinels ─────────────────────────────────────────────────────────────────

VALID_CONFIDENCE_BANDS: frozenset[str] = frozenset({"High", "Medium", "Low"})

REQUIRED_CONFIDENCE_DIMENSIONS: frozenset[str] = frozenset(
    {
        "evidence_strength",
        "relevance",
        "freshness",
        "transferability",
        "contradiction_pressure",
    }
)

VALID_RECOMMENDATION_CLASSES: frozenset[str] = frozenset(
    {"Preventive", "Corrective", "Optimizing", "Learning-Oriented"}
)

# ── Canonical signal types (ACL translation outputs) ─────────────────────────
# These are the only types that may cross the ERPNext context reader boundary.
# No ERPNext field names, DocType names, or approval-state strings may appear
# outside the reader module itself.


@dataclass(frozen=True)
class CanonicalDecisionSignal:
    """An open Decision Record expressed in canonical ontology terms."""

    name: str
    state: str         # Draft / Submitted for Approval / Approved / Rejected
    criticality: str   # Low / Medium / High
    decision_type: str  # Operational / Strategic
    owner: str


@dataclass(frozen=True)
class CanonicalDependencySignal:
    """An unresolved Dependency Exception Record in canonical ontology terms."""

    name: str
    criticality: str    # Low / Medium / High / Critical
    status: str         # Open / At Risk
    dependency_type: str  # Team / System / Vendor / Data / Policy
    days_overdue: int   # 0 when resolution date has not yet been breached


@dataclass(frozen=True)
class CanonicalKPISignal:
    """A KPI baseline signal drawn from the charter's baseline KPI child table."""

    kpi_code: str       # DRR / DCT / AER / OCR / RER
    baseline_value: float
    data_source: str


@dataclass(frozen=True)
class CanonicalActionSignal:
    """An overdue commitment signal, proxied from ERPNext Task records."""

    name: str
    overdue_days: int
    owner: str


@dataclass(frozen=True)
class CharterContext:
    """Aggregate canonical context for one Lighthouse Workflow Charter.

    Invariant: all fields use canonical ontology terms only.  No ERPNext-
    specific terminology escapes the context reader's ACL boundary.
    """

    charter_name: str
    business_objective: str
    in_scope_definition: str
    open_decisions: tuple[CanonicalDecisionSignal, ...]
    open_dependencies: tuple[CanonicalDependencySignal, ...]
    kpi_signals: tuple[CanonicalKPISignal, ...]
    overdue_actions: tuple[CanonicalActionSignal, ...]

    def __post_init__(self) -> None:
        if not self.charter_name:
            raise ValueError("charter_name must not be empty")
        if not self.business_objective:
            raise ValueError("business_objective must not be empty")


# ── Recommendation value objects ─────────────────────────────────────────────


@dataclass(frozen=True)
class VerificationPlan:
    """Pre-execution verification contract required by Phase 6 §11.1."""

    baseline: str
    expected_kpi_direction: str  # Increase / Decrease / Stable
    review_window: str
    acceptance_criteria: str


@dataclass
class ConfidenceState:
    """Calibrated confidence state required by Phase 6 §7.

    All five approved confidence dimensions must be present.
    Band is restricted to the three canonical values.
    """

    band: str                    # High / Medium / Low
    rationale: str               # summary rationale for the band
    dimensions: dict[str, str]   # evidence_strength, relevance, freshness,
                                 # transferability, contradiction_pressure

    def __post_init__(self) -> None:
        if self.band not in VALID_CONFIDENCE_BANDS:
            raise ValueError(
                f"confidence band must be one of {sorted(VALID_CONFIDENCE_BANDS)}, got {self.band!r}"
            )
        if not self.rationale:
            raise ValueError("confidence rationale must not be empty")
        missing = REQUIRED_CONFIDENCE_DIMENSIONS - set(self.dimensions)
        if missing:
            raise ValueError(
                f"confidence dimensions missing required keys: {sorted(missing)}"
            )


@dataclass
class Recommendation:
    """A single AI-generated decision recommendation.

    Conforms to the nine-field recommendation object specified in
    PHASE_6_AI_REASONING_ARCHITECTURE_MODEL_AGNOSTIC.md §10.1.

    Governance invariants enforced here:
      - assumptions must be non-empty (Phase 6 invariant 2; ontology invariant I5)
      - causal_hypothesis must follow the approved grammar and contain '→'
      - recommendation_class must be one of the four approved classes
    """

    index: int
    recommendation_class: str      # Preventive / Corrective / Optimizing / Learning-Oriented
    objective_served: str          # field 1
    assumptions: list[str]         # field 2 — min 1 non-empty entry
    expected_value_hypothesis: str  # field 3
    trade_offs: list[str]          # field 4
    risk_exposure: str             # field 5
    dependency_implications: str   # field 6
    confidence_state: ConfidenceState   # field 7
    verification_plan: VerificationPlan  # field 8
    owner_and_review_point: str    # field 9
    causal_hypothesis: str         # "If [assumption] + [context] → [action] → [outcome] + [value]"

    def __post_init__(self) -> None:
        if self.recommendation_class not in VALID_RECOMMENDATION_CLASSES:
            raise ValueError(
                f"recommendation_class must be one of {sorted(VALID_RECOMMENDATION_CLASSES)}, "
                f"got {self.recommendation_class!r}"
            )
        if not self.assumptions:
            raise ValueError(
                "assumptions must contain at least one entry "
                "(Phase 6 invariant: no recommendation without explicit assumptions)"
            )
        if any(not a.strip() for a in self.assumptions):
            raise ValueError("every assumption entry must be a non-empty string")
        if not self.objective_served:
            raise ValueError("objective_served must not be empty")
        if not self.causal_hypothesis:
            raise ValueError("causal_hypothesis must not be empty")
        if "\u2192" not in self.causal_hypothesis:  # → (U+2192)
            raise ValueError(
                "causal_hypothesis must contain the causal arrow '\u2192' "
                "per the approved grammar: Assumption + Context \u2192 Action \u2192 Outcome + Value"
            )


@dataclass
class RecommendationPackage:
    """Complete output of one agent execution cycle.

    Contains 0–N recommendations plus metadata needed for the reasoning trace.
    The recommendations list is empty (not an error) when the charter has no
    context signals to reason over.
    """

    charter_name: str
    recommendations: list[Recommendation]
    context_snapshot: dict[str, Any]  # JSON-safe snapshot of CharterContext
    model_identifier: str             # e.g., "ollama:llama3.2" or "null:deterministic"
    fallback_used: bool
    execution_timestamp: str          # ISO-8601

    def __post_init__(self) -> None:
        if not self.charter_name:
            raise ValueError("charter_name must not be empty")
        if not self.model_identifier:
            raise ValueError("model_identifier must not be empty")
        if not self.execution_timestamp:
            raise ValueError("execution_timestamp must not be empty")

    def to_api_dict(self) -> dict[str, Any]:
        """Return a JSON-safe dict suitable for Frappe API responses."""
        return {
            "charter_name": self.charter_name,
            "recommendations": [recommendation_to_dict(r) for r in self.recommendations],
            "context_snapshot": self.context_snapshot,
            "model_identifier": self.model_identifier,
            "fallback_used": self.fallback_used,
            "execution_timestamp": self.execution_timestamp,
        }


# ── Serialisation helpers ─────────────────────────────────────────────────────


def recommendation_to_dict(r: Recommendation) -> dict[str, Any]:
    """Convert a Recommendation to a JSON-safe dict for API transport."""
    return {
        "index": r.index,
        "recommendation_class": r.recommendation_class,
        "objective_served": r.objective_served,
        "assumptions": list(r.assumptions),
        "expected_value_hypothesis": r.expected_value_hypothesis,
        "trade_offs": list(r.trade_offs),
        "risk_exposure": r.risk_exposure,
        "dependency_implications": r.dependency_implications,
        "confidence_state": {
            "band": r.confidence_state.band,
            "rationale": r.confidence_state.rationale,
            "dimensions": dict(r.confidence_state.dimensions),
        },
        "verification_plan": {
            "baseline": r.verification_plan.baseline,
            "expected_kpi_direction": r.verification_plan.expected_kpi_direction,
            "review_window": r.verification_plan.review_window,
            "acceptance_criteria": r.verification_plan.acceptance_criteria,
        },
        "owner_and_review_point": r.owner_and_review_point,
        "causal_hypothesis": r.causal_hypothesis,
    }


def charter_context_to_snapshot(ctx: CharterContext) -> dict[str, Any]:
    """Convert a CharterContext to a JSON-safe dict for reasoning trace storage."""
    return {
        "charter_name": ctx.charter_name,
        "business_objective": ctx.business_objective,
        "in_scope_definition": ctx.in_scope_definition,
        "open_decisions": [
            {
                "name": d.name,
                "state": d.state,
                "criticality": d.criticality,
                "decision_type": d.decision_type,
                "owner": d.owner,
            }
            for d in ctx.open_decisions
        ],
        "open_dependencies": [
            {
                "name": d.name,
                "criticality": d.criticality,
                "status": d.status,
                "dependency_type": d.dependency_type,
                "days_overdue": d.days_overdue,
            }
            for d in ctx.open_dependencies
        ],
        "kpi_signals": [
            {
                "kpi_code": k.kpi_code,
                "baseline_value": k.baseline_value,
                "data_source": k.data_source,
            }
            for k in ctx.kpi_signals
        ],
        "overdue_actions": [
            {"name": a.name, "overdue_days": a.overdue_days, "owner": a.owner}
            for a in ctx.overdue_actions
        ],
    }


def recommendation_from_dict(data: dict[str, Any]) -> Recommendation:
    """Reconstruct a Recommendation from an API transport dict (accept/reject flow)."""
    cs_raw = data["confidence_state"]
    vp_raw = data["verification_plan"]
    return Recommendation(
        index=int(data["index"]),
        recommendation_class=data["recommendation_class"],
        objective_served=data["objective_served"],
        assumptions=list(data["assumptions"]),
        expected_value_hypothesis=data["expected_value_hypothesis"],
        trade_offs=list(data.get("trade_offs", [])),
        risk_exposure=data["risk_exposure"],
        dependency_implications=data["dependency_implications"],
        confidence_state=ConfidenceState(
            band=cs_raw["band"],
            rationale=cs_raw["rationale"],
            dimensions=dict(cs_raw["dimensions"]),
        ),
        verification_plan=VerificationPlan(
            baseline=vp_raw["baseline"],
            expected_kpi_direction=vp_raw["expected_kpi_direction"],
            review_window=vp_raw["review_window"],
            acceptance_criteria=vp_raw["acceptance_criteria"],
        ),
        owner_and_review_point=data["owner_and_review_point"],
        causal_hypothesis=data["causal_hypothesis"],
    )


# ── Intermediate reasoning pipeline types ────────────────────────────────────
# These dataclasses form the typed contracts between R1–R6 reasoning layers.
# They live here because they are domain contracts, not layer-specific details.


@dataclass(frozen=True)
class IntentFrame:
    """Output of R1 Intent Framing. Contains governance intent only — no recommendations."""

    objective: str
    constraints: tuple[str, ...]
    priorities: tuple[str, ...]
    scope_summary: str

    def __post_init__(self) -> None:
        if not self.objective:
            raise ValueError("IntentFrame objective must not be empty")
        if not self.scope_summary:
            raise ValueError("IntentFrame scope_summary must not be empty")


@dataclass(frozen=True)
class SituationAssessment:
    """Output of R2 Situation Interpretation. Contains observations only — no decisions."""

    observations: tuple[str, ...]
    risk_indicators: tuple[str, ...]
    opportunity_indicators: tuple[str, ...]
    context_summary: str

    def __post_init__(self) -> None:
        if not self.context_summary:
            raise ValueError("SituationAssessment context_summary must not be empty")


@dataclass(frozen=True)
class CausalHypothesis:
    """Output element of R3 Causal Hypothesis Construction.

    Follows the approved grammar:
    'If [assumption] + [context_conditions] → [proposed_action] → [expected_outcome] + [value_effect]'
    """

    assumption: str
    context_conditions: str
    proposed_action: str
    expected_outcome: str
    value_effect: str
    hypothesis_text: str       # full grammar string; must contain '→'
    recommendation_class: str  # propagated to R4 DecisionOption

    def __post_init__(self) -> None:
        if not self.assumption:
            raise ValueError("CausalHypothesis assumption must not be empty")
        if not self.hypothesis_text:
            raise ValueError("CausalHypothesis hypothesis_text must not be empty")
        if "\u2192" not in self.hypothesis_text:
            raise ValueError("CausalHypothesis hypothesis_text must contain '\u2192'")
        if self.recommendation_class not in VALID_RECOMMENDATION_CLASSES:
            raise ValueError(
                f"recommendation_class must be one of {sorted(VALID_RECOMMENDATION_CLASSES)}"
            )


@dataclass(frozen=True)
class DecisionOption:
    """Output element of R4 Option Generation.

    Carries all fields needed to build a Recommendation except confidence;
    confidence is added by R5.
    """

    hypothesis: CausalHypothesis
    recommendation_class: str
    objective_served: str
    expected_value_hypothesis: str
    trade_offs: tuple[str, ...]
    risk_exposure: str
    dependency_implications: str
    owner_and_review_point: str
    verification_baseline: str
    verification_kpi_direction: str   # Increase / Decrease / Stable
    verification_review_window: str
    verification_acceptance_criteria: str

    def __post_init__(self) -> None:
        if self.recommendation_class not in VALID_RECOMMENDATION_CLASSES:
            raise ValueError(
                f"recommendation_class must be one of {sorted(VALID_RECOMMENDATION_CLASSES)}"
            )
        if not self.objective_served:
            raise ValueError("DecisionOption objective_served must not be empty")


@dataclass
class CalibratedDecisionOption:
    """Output element of R5 Confidence Calibration.

    Wraps a DecisionOption and adds the five-dimension confidence state.
    Only R6 converts this into a final Recommendation.
    """

    option: DecisionOption
    confidence_band: str                 # High / Medium / Low
    confidence_rationale: str
    confidence_dimensions: dict[str, str]  # five required keys

    def __post_init__(self) -> None:
        if self.confidence_band not in VALID_CONFIDENCE_BANDS:
            raise ValueError(
                f"confidence_band must be one of {sorted(VALID_CONFIDENCE_BANDS)}"
            )
        if not self.confidence_rationale:
            raise ValueError("confidence_rationale must not be empty")
        missing = REQUIRED_CONFIDENCE_DIMENSIONS - set(self.confidence_dimensions)
        if missing:
            raise ValueError(
                f"confidence_dimensions missing required keys: {sorted(missing)}"
            )
