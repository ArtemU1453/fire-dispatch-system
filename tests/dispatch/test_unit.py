"""Unit tests for the Dispatch Engine internals (no database).

Covers requirement aggregation, capability analysis, scoring, the selection
strategy, coverage validation, priority resolution and request validation.
"""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationError
from app.dispatch.algorithms.candidate import DispatchCandidate
from app.dispatch.algorithms.capability_analyzer import CapabilityAnalyzer
from app.dispatch.algorithms.coverage_validator import CoverageValidator
from app.dispatch.algorithms.priority_resolver import PriorityResolver
from app.dispatch.algorithms.scoring import Scorer
from app.dispatch.config import DispatchConfig
from app.dispatch.recommendations.models import CapabilityCoverage
from app.dispatch.requirements import (
    CapabilityNeed,
    RequirementAggregator,
    RequirementSet,
)
from app.dispatch.schemas.requests import DispatchConstraints, DispatchRequest
from app.dispatch.strategies import GreedyCapabilitySelectionStrategy
from app.dispatch.validators import DispatchValidator
from app.models.enums import ResourceCategory
from app.rules.engine import ApplicableRule
from app.rules.models.entities import (
    CapabilityRequirement,
    ResourceRequirement,
    Rule,
    RuleVersion,
)
from app.rules.models.enums import RulePriority


def _candidate(caps: dict[str, int], *, distance=100.0, readiness="deployable"):
    return DispatchCandidate(
        resource=SimpleNamespace(id=uuid4()),
        distance_meters=distance,
        readiness=readiness,
        capabilities=caps,
    )


def _applicable(priority, res_reqs, cap_reqs) -> ApplicableRule:
    version = RuleVersion(priority=priority)
    version.resource_requirements = [
        ResourceRequirement(
            resource_category=cat, min_count=mn, recommended_count=rc,
            reserve_count=rs, is_deleted=False,
        )
        for cat, mn, rc, rs in res_reqs
    ]
    version.capability_requirements = [
        CapabilityRequirement(
            capability_code=code, min_quantity=q, mandatory=m, is_deleted=False
        )
        for code, q, m in cap_reqs
    ]
    return ApplicableRule(rule=Rule(id=uuid4(), code="R"), version=version)


# --------------------------------------------------------------- aggregator ---
def test_aggregator_takes_elementwise_max_and_union() -> None:
    r1 = _applicable(
        RulePriority.NORMAL,
        [(ResourceCategory.VEHICLE, 1, 2, 0)],
        [("fire_suppression", 1, True)],
    )
    r2 = _applicable(
        RulePriority.HIGH,
        [(ResourceCategory.VEHICLE, 2, 2, 1)],
        [("fire_suppression", 2, False), ("water_supply", 1, True)],
    )
    result = RequirementAggregator().aggregate([r1, r2])

    assert result.category_minimum[ResourceCategory.VEHICLE] == 2
    assert result.category_recommended[ResourceCategory.VEHICLE] == 2
    assert result.category_reserve[ResourceCategory.VEHICLE] == 1
    # mandatory wins, min_quantity is the strictest.
    assert result.capabilities["fire_suppression"].min_quantity == 2
    assert result.capabilities["fire_suppression"].mandatory is True
    assert result.priority is RulePriority.HIGH
    assert set(result.required_capability_codes) == {"fire_suppression", "water_supply"}


def test_aggregator_empty_is_harmless() -> None:
    result = RequirementAggregator().aggregate([])
    assert not result.has_requirements
    assert result.minimum_units == 0


# ------------------------------------------------------------ capability -----
def test_capability_coverage_counts_provided() -> None:
    analyzer = CapabilityAnalyzer()
    req = RequirementSet(
        capabilities={
            "fire_suppression": CapabilityNeed("fire_suppression", 2, True),
        }
    )
    units = [_candidate({"fire_suppression": 1}), _candidate({"fire_suppression": 1})]
    coverage = analyzer.coverage(req, units, {"fire_suppression": "Пожаротушение"})
    assert coverage[0].provided == 2
    assert coverage[0].satisfied is True
    assert coverage[0].label == "Пожаротушение"


def test_provides_any_required_true_when_no_requirements() -> None:
    analyzer = CapabilityAnalyzer()
    empty = RequirementSet()
    assert analyzer.provides_any_required(_candidate({}), empty) is True
    req = RequirementSet(
        capabilities={"x": CapabilityNeed("x", 1, True)}
    )
    assert analyzer.provides_any_required(_candidate({"y": 1}), req) is False


# --------------------------------------------------------------- scoring -----
def test_scorer_produces_bounded_score_without_eta() -> None:
    scorer = Scorer(DispatchConfig(), ["fire_suppression"])
    near = scorer.score(
        distance_meters=100, readiness="deployable",
        capabilities={"fire_suppression": 1},
    )
    far = scorer.score(
        distance_meters=25000, readiness="deployable",
        capabilities={"fire_suppression": 1},
    )
    assert 0.0 <= far.total <= near.total <= 1.0
    assert "arrival_time" not in near.breakdown  # no ETA provider at this stage


# ------------------------------------------------------------- selection -----
def test_greedy_selection_tops_up_for_mandatory_capability() -> None:
    req = RequirementSet(
        resource_categories={ResourceCategory.VEHICLE},
        capabilities={"foam": CapabilityNeed("foam", 1, True)},
        category_minimum={ResourceCategory.VEHICLE: 1},
        category_recommended={ResourceCategory.VEHICLE: 2},
    )
    c1 = _candidate({}, distance=50)
    c2 = _candidate({}, distance=60)
    c3 = _candidate({"foam": 1}, distance=500)  # only unit with the capability
    selected = GreedyCapabilitySelectionStrategy().select(req, [c1, c2, c3])
    ids = {c.id for c in selected}
    assert c3.id in ids  # topped up to cover 'foam'
    assert c1.id in ids and c2.id in ids


# ------------------------------------------------------------- coverage ------
def test_coverage_validator_flags_missing_mandatory() -> None:
    req = RequirementSet(
        capabilities={"foam": CapabilityNeed("foam", 1, True)},
        category_minimum={ResourceCategory.VEHICLE: 1},
    )
    coverage = [CapabilityCoverage("foam", "Пена", required=1, provided=0)]
    sufficient, messages = CoverageValidator().validate(req, 1, coverage)
    assert sufficient is False
    assert any("foam" in m or "Пена" in m for m in messages)


def test_coverage_validator_no_resources() -> None:
    sufficient, messages = CoverageValidator().validate(RequirementSet(), 0, [])
    assert sufficient is False
    assert any("не найдено" in m.lower() for m in messages)


# ------------------------------------------------------------- priority ------
def test_priority_floor_from_danger_level() -> None:
    resolver = PriorityResolver()
    req = RequirementSet(priority=RulePriority.NORMAL)
    assert resolver.resolve(req, "critical") is RulePriority.CRITICAL
    assert resolver.resolve(req, None) is RulePriority.NORMAL


def test_rank_candidates_orders_by_score() -> None:
    lo = _candidate({}, distance=100)
    hi = _candidate({}, distance=100)
    from app.dispatch.algorithms.scoring import RecommendationScore

    lo.score = RecommendationScore(total=0.2)
    hi.score = RecommendationScore(total=0.9)
    ranked = PriorityResolver.rank_candidates([lo, hi])
    assert ranked[0] is hi


# ------------------------------------------------------------- validator -----
def test_request_validator_requires_location() -> None:
    request = DispatchRequest(incident_type_id=uuid4())
    with pytest.raises(ValidationError):
        DispatchValidator().validate(request)


def test_request_validator_accepts_coordinates() -> None:
    request = DispatchRequest(
        incident_type_id=uuid4(),
        latitude=55.75,
        longitude=37.62,
        constraints=DispatchConstraints(),
    )
    DispatchValidator().validate(request)  # no raise


# ------------------------------------------------------- exclusion (engine) ---
def _status(*, operational=True, deployable=True, code="ok"):
    return SimpleNamespace(
        is_operational=operational,
        is_available_for_dispatch=deployable,
        code=code,
    )


def _engine():
    from app.dispatch.engine import DispatchEngine

    return DispatchEngine.__new__(DispatchEngine)  # bypass __init__ for pure helpers


def _zone_candidate(caps, *, status, service_area_ids=frozenset()):
    from uuid import uuid4 as _u

    return DispatchCandidate(
        resource=SimpleNamespace(id=_u(), availability_status=status),
        distance_meters=100.0,
        readiness="deployable",
        capabilities=caps,
        service_area_ids=set(service_area_ids),
    )


def _make_engine():
    from app.dispatch.config import DispatchConfig

    eng = _engine()
    eng._config = DispatchConfig()
    eng._analyzer = CapabilityAnalyzer()
    return eng


def test_exclusion_unavailable_and_capability_and_manual() -> None:
    from app.dispatch.engine import IncidentContext
    from app.dispatch.models.enums import ExclusionReason

    eng = _make_engine()
    req = RequirementSet(capabilities={"fs": CapabilityNeed("fs", 1, True)})
    incident = IncidentContext(
        incident_type_id=uuid4(), latitude=0.0, longitude=0.0
    )

    ok = _zone_candidate({"fs": 1}, status=_status())
    not_deployable = _zone_candidate({"fs": 1}, status=_status(deployable=False))
    no_cap = _zone_candidate({"other": 1}, status=_status())

    incident.excluded_resource_ids = {ok.id}
    eligible, excluded = eng._partition([ok, not_deployable, no_cap], req, incident)

    reasons = {e.candidate.id: e.reason for e in excluded}
    assert reasons[ok.id] is ExclusionReason.MANUAL_EXCLUSION
    assert reasons[not_deployable.id] is ExclusionReason.NOT_DEPLOYABLE
    assert reasons[no_cap.id] is ExclusionReason.MISSING_CAPABILITY
    assert eligible == []


def test_exclusion_out_of_service_zone() -> None:
    from app.dispatch.engine import IncidentContext
    from app.dispatch.models.enums import ExclusionReason

    eng = _make_engine()
    req = RequirementSet(capabilities={"fs": CapabilityNeed("fs", 1, True)})
    area = uuid4()
    incident = IncidentContext(
        incident_type_id=uuid4(), latitude=0.0, longitude=0.0,
        administrative_area_id=area,
    )
    in_zone = _zone_candidate({"fs": 1}, status=_status(), service_area_ids={area})
    out_zone = _zone_candidate(
        {"fs": 1}, status=_status(), service_area_ids={uuid4()}
    )
    everywhere = _zone_candidate({"fs": 1}, status=_status())  # no zones → serves all

    eligible, excluded = eng._partition([in_zone, out_zone, everywhere], req, incident)
    eligible_ids = {c.id for c in eligible}
    assert in_zone.id in eligible_ids
    assert everywhere.id in eligible_ids
    assert excluded[0].candidate.id == out_zone.id
    assert excluded[0].reason is ExclusionReason.OUT_OF_SERVICE_ZONE
