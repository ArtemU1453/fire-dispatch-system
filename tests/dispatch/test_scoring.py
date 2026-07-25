"""Unit tests for the configurable scorer (no DB)."""

from __future__ import annotations

import pytest

from app.dispatch.algorithms.scoring import (
    READY_DEPLOYABLE,
    READY_OTHER,
    Scorer,
)
from app.dispatch.rules.models import ScoringConfig


def test_distance_score_decays_to_zero_at_max() -> None:
    cfg = ScoringConfig(max_distance_meters=10000)
    scorer = Scorer(cfg)
    near = scorer.score(distance_meters=0, readiness=READY_DEPLOYABLE, capabilities={})
    far = scorer.score(
        distance_meters=10000, readiness=READY_DEPLOYABLE, capabilities={}
    )
    assert near.breakdown["distance"] == pytest.approx(1.0)
    assert far.breakdown["distance"] == pytest.approx(0.0)


def test_readiness_uses_config() -> None:
    cfg = ScoringConfig()
    scorer = Scorer(cfg)
    deployable = scorer.score(
        distance_meters=0, readiness=READY_DEPLOYABLE, capabilities={}
    )
    other = scorer.score(distance_meters=0, readiness=READY_OTHER, capabilities={})
    assert deployable.breakdown["readiness"] == pytest.approx(1.0)
    assert other.breakdown["readiness"] == pytest.approx(0.0)


def test_capability_match_is_fraction_of_required() -> None:
    scorer = Scorer(ScoringConfig(), required_capabilities=["a", "b"])
    score = scorer.score(
        distance_meters=0, readiness=READY_DEPLOYABLE, capabilities={"a": 1}
    )
    assert score.breakdown["capability_match"] == pytest.approx(0.5)


def test_no_required_capabilities_scores_full_match() -> None:
    scorer = Scorer(ScoringConfig(), required_capabilities=[])
    score = scorer.score(
        distance_meters=0, readiness=READY_DEPLOYABLE, capabilities={}
    )
    assert score.breakdown["capability_match"] == pytest.approx(1.0)


def test_arrival_weight_excluded_when_no_estimate() -> None:
    # With default weights and no arrival estimate, the total renormalizes over
    # the active components only (arrival does not drag the score down).
    scorer = Scorer(ScoringConfig(), required_capabilities=["a"])
    score = scorer.score(
        distance_meters=0, readiness=READY_DEPLOYABLE, capabilities={"a": 1}
    )
    # distance=1, readiness=1, capability=1, weights 0.5/0.2/0.2 → total 1.0
    assert "arrival_time" not in score.breakdown
    assert score.total == pytest.approx(1.0)


def test_weights_are_configurable() -> None:
    cfg = ScoringConfig()
    cfg.weights.distance = 1.0
    cfg.weights.readiness = 0.0
    cfg.weights.capability_match = 0.0
    scorer = Scorer(cfg)
    score = scorer.score(
        distance_meters=0, readiness=READY_OTHER, capabilities={}
    )
    # Only distance matters now.
    assert score.total == pytest.approx(1.0)
