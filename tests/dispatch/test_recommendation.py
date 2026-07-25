"""Unit tests for the RecommendationEngine composition (no DB)."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from app.dispatch.algorithms.candidate import DispatchCandidate
from app.dispatch.algorithms.scoring import READY_DEPLOYABLE, RecommendationScore
from app.dispatch.recommendations import RecommendationEngine
from app.dispatch.rules.models import (
    CapabilityRequirement,
    IncidentRule,
    ScoringConfig,
)
from app.models.enums import ResourceCategory


def _candidate(
    caps: dict[str, int], score: float, distance: float
) -> DispatchCandidate:
    c = DispatchCandidate(
        resource=SimpleNamespace(id=uuid4()),  # type: ignore[arg-type]
        distance_meters=distance,
        readiness=READY_DEPLOYABLE,
        capabilities=caps,
    )
    c.score = RecommendationScore(total=score, reasons=["r"])
    return c


_RULE = IncidentRule(
    code="fire",
    name="Пожар",
    priority=1,
    resource_categories=[ResourceCategory.VEHICLE],
    required_capabilities=[
        CapabilityRequirement(code="fire_suppression", min_quantity=2),
        CapabilityRequirement(code="water_supply", min_quantity=1),
    ],
    minimum_units=2,
    recommended_units=3,
    reserve_units=1,
)


def _engine() -> RecommendationEngine:
    return RecommendationEngine(ScoringConfig())


def test_sufficient_when_requirements_met() -> None:
    candidates = [
        _candidate({"fire_suppression": 1, "water_supply": 1}, 0.9, 100),
        _candidate({"fire_suppression": 1}, 0.8, 200),
        _candidate({"fire_suppression": 1}, 0.7, 300),
        _candidate({"fire_suppression": 1}, 0.6, 400),  # spare → reserve
    ]
    rec = _engine().build(
        rule=_RULE, latitude=55.0, longitude=37.0, candidates=candidates
    )
    assert rec.sufficient is True
    coverage = {c.code: c for c in rec.capability_coverage}
    assert coverage["fire_suppression"].provided >= 2
    assert coverage["water_supply"].satisfied
    assert len(rec.primary_units) >= 2
    # recommended_units=3 → 3 primary, reserve_units=1 → 1 reserve.
    assert len(rec.reserve_units) == 1


def test_insufficient_when_capability_missing() -> None:
    candidates = [
        _candidate({"fire_suppression": 1}, 0.9, 100),
        _candidate({"fire_suppression": 1}, 0.8, 200),
    ]
    rec = _engine().build(
        rule=_RULE, latitude=55.0, longitude=37.0, candidates=candidates
    )
    assert rec.sufficient is False
    assert any("Водоснабжение" in m or "water_supply" in m for m in rec.messages)


def test_insufficient_when_too_few_units() -> None:
    candidates = [_candidate({"fire_suppression": 2, "water_supply": 1}, 0.9, 100)]
    rec = _engine().build(
        rule=_RULE, latitude=55.0, longitude=37.0, candidates=candidates
    )
    # Capabilities covered by one unit, but minimum_units is 2.
    assert rec.sufficient is False
    assert any("Недостаточно единиц" in m for m in rec.messages)


def test_empty_candidates() -> None:
    rec = _engine().build(rule=_RULE, latitude=55.0, longitude=37.0, candidates=[])
    assert rec.sufficient is False
    assert rec.total_candidates == 0
    assert rec.primary_units == []


def test_preview_has_no_reserves() -> None:
    candidates = [
        _candidate({"fire_suppression": 1, "water_supply": 1}, 0.9, 100),
        _candidate({"fire_suppression": 1}, 0.8, 200),
    ]
    rec = _engine().build(
        rule=_RULE, latitude=55.0, longitude=37.0, candidates=candidates, preview=True
    )
    assert rec.is_preview is True
    assert rec.reserve_units == []


def test_confidence_label_from_thresholds() -> None:
    candidates = [
        _candidate({"fire_suppression": 2, "water_supply": 1}, 1.0, 10),
        _candidate({"fire_suppression": 1, "water_supply": 1}, 1.0, 20),
        _candidate({"fire_suppression": 1, "water_supply": 1}, 1.0, 30),
    ]
    rec = _engine().build(
        rule=_RULE, latitude=55.0, longitude=37.0, candidates=candidates
    )
    assert rec.confidence == "high"
