"""Mapping between dispatch domain objects and API schemas."""

from __future__ import annotations

from app.dispatch.recommendations.models import Recommendation as DomainRecommendation
from app.dispatch.recommendations.models import RecommendedUnit
from app.dispatch.rules.models import IncidentRule
from app.dispatch.schemas.responses import (
    CapabilityCoverageItem,
    CapabilityRequirement,
    DispatchPoint,
    DispatchResponse,
    Recommendation,
    RecommendationItem,
    RefLabel,
    RuleResponse,
)


def _unit_to_item(unit: RecommendedUnit) -> RecommendationItem:
    c = unit.candidate
    r = c.resource
    rt, org, st = r.resource_type, r.organization, r.availability_status
    return RecommendationItem(
        id=r.id,
        code=r.code,
        name=r.name,
        role=unit.role,
        distance_meters=c.distance_meters,
        score=c.score_value if c.score is not None else None,
        readiness=c.readiness,
        capabilities=sorted(c.capabilities.keys()),
        reasons=unit.reasons,
        resource_type=(
            RefLabel(id=rt.id, code=rt.code, name=rt.name) if rt is not None else None
        ),
        organization=(
            RefLabel(id=org.id, code=org.code, name=org.name)
            if org is not None
            else None
        ),
        availability_status=(
            RefLabel(id=st.id, code=st.code, name=st.name) if st is not None else None
        ),
    )


def to_dispatch_response(rec: DomainRecommendation) -> DispatchResponse:
    recommendation = Recommendation(
        sufficient=rec.sufficient,
        confidence=rec.confidence,
        confidence_score=rec.confidence_score,
        primary_units=[_unit_to_item(u) for u in rec.primary_units],
        reserve_units=[_unit_to_item(u) for u in rec.reserve_units],
        capability_coverage=[
            CapabilityCoverageItem(
                code=cov.code,
                label=cov.label,
                required=cov.required,
                provided=cov.provided,
                satisfied=cov.satisfied,
            )
            for cov in rec.capability_coverage
        ],
        messages=rec.messages,
        is_preview=rec.is_preview,
    )
    return DispatchResponse(
        incident_type=rec.incident_type,
        incident_name=rec.incident_name,
        priority=rec.priority,
        point=DispatchPoint(latitude=rec.latitude, longitude=rec.longitude),
        total_candidates=rec.total_candidates,
        recommendation=recommendation,
    )


def rule_to_response(rule: IncidentRule) -> RuleResponse:
    return RuleResponse(
        code=rule.code,
        name=rule.name,
        priority=rule.priority,
        resource_categories=rule.resource_categories,
        required_capabilities=[
            CapabilityRequirement(
                code=req.code, min_quantity=req.min_quantity, label=req.label
            )
            for req in rule.required_capabilities
        ],
        minimum_units=rule.minimum_units,
        recommended_units=rule.recommended_units,
        reserve_units=rule.reserve_units,
        search_radius_meters=rule.search_radius_meters,
    )
