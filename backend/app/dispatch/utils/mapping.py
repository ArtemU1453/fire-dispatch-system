"""Mapping between dispatch domain objects, ORM rows and API schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from app.dispatch.models.entities import (
    CapabilityMatch,
    DispatchDecision,
    RecommendationSummary,
    ResourceMatch,
)
from app.dispatch.models.entities import (
    Recommendation as RecommendationORM,
)
from app.dispatch.models.entities import (
    RecommendationItem as RecommendationItemORM,
)
from app.dispatch.models.entities import (
    RecommendationReason as RecommendationReasonORM,
)
from app.dispatch.models.enums import ExclusionReason, RecommendationRole
from app.dispatch.recommendations.models import RecommendedUnit
from app.dispatch.schemas.responses import (
    CapabilityCoverageItem,
    CapabilityResponse,
    DispatchPoint,
    RecommendationHistoryItem,
    RecommendationItem,
    RecommendationResponse,
    RecommendationSummaryResponse,
    RefLabel,
    ResourceMatchResponse,
)
from app.rules.models.enums import IncidentComplexity

if TYPE_CHECKING:
    from app.dispatch.engine import DispatchOutcome


# --------------------------------------------------------------- domain → ORM
def outcome_to_orm(
    outcome: DispatchOutcome,
    *,
    incident_id: UUID | None,
    complexity: IncidentComplexity | None,
    address: str | None,
    administrative_area_id: UUID | None,
    danger_level: str | None,
    request_snapshot: dict[str, Any],
) -> RecommendationORM:
    """Build the persistent aggregate (unattached) from an engine outcome."""
    rec = outcome.recommendation
    orm = RecommendationORM(
        incident_id=incident_id,
        incident_type_id=rec.incident_type_id,
        complexity=complexity,
        latitude=rec.latitude,
        longitude=rec.longitude,
        address=address,
        administrative_area_id=administrative_area_id,
        danger_level=danger_level,
        priority=rec.priority,
        status=rec.status,
        sufficient=rec.sufficient,
        confidence=rec.confidence,
        confidence_score=rec.confidence_score,
        total_candidates=rec.total_candidates,
        is_preview=rec.is_preview,
    )

    # Items (primary + reserve) with their reasons. Each item-level reason is
    # linked to both the item (item_id) and the recommendation (recommendation_id,
    # which is NOT NULL) by adding it to both collections.
    order = 0
    for unit in [*rec.primary_units, *rec.reserve_units]:
        item = _item_orm(unit, order)
        orm.items.append(item)
        orm.reasons.extend(item.reasons)
        order += 1

    # Global (recommendation-level) reasons.
    for text in rec.global_reasons:
        orm.reasons.append(RecommendationReasonORM(text=text, kind="global"))

    # Capability coverage.
    for cov in rec.capability_coverage:
        orm.capability_matches.append(
            CapabilityMatch(
                capability_code=cov.code,
                required_quantity=cov.required,
                provided_quantity=cov.provided,
                satisfied=cov.satisfied,
                mandatory=cov.mandatory,
            )
        )

    # Resource-match log: selected, not-selected (eligible) and excluded.
    orm.resource_matches.extend(_resource_matches(outcome))

    # Roll-up summary.
    covered = sorted(c.code for c in rec.capability_coverage if c.satisfied)
    missing = sorted(c.code for c in rec.capability_coverage if not c.satisfied)
    orm.summary = RecommendationSummary(
        primary_count=len(rec.primary_units),
        reserve_count=len(rec.reserve_units),
        minimum_units=rec.minimum_units,
        recommended_units=rec.recommended_units,
        reserve_units=rec.reserve_units_target,
        required_capabilities=[c.code for c in rec.capability_coverage],
        covered_capabilities=covered,
        missing_capabilities=missing,
        messages=list(rec.messages),
    )

    # Decision / audit log (advisory — never auto-decided).
    orm.decision = DispatchDecision(
        incident_id=incident_id,
        decided=False,
        status=rec.status,
        used_rule_ids=[str(r) for r in rec.rule_ids],
        used_rule_codes=list(rec.rule_codes),
        request_snapshot=request_snapshot,
    )
    return orm


def _item_orm(unit: RecommendedUnit, order: int) -> RecommendationItemORM:
    candidate = unit.candidate
    item = RecommendationItemORM(
        resource_id=candidate.id,
        role=unit.role,
        distance_meters=candidate.distance_meters,
        score=candidate.score_value if candidate.score is not None else None,
        readiness=candidate.readiness,
        sort_order=order,
    )
    for text in unit.reasons:
        item.reasons.append(RecommendationReasonORM(text=text, kind="selection"))
    return item


def _resource_matches(outcome: DispatchOutcome) -> list[ResourceMatch]:
    matches: list[ResourceMatch] = []
    selected = outcome.selected_ids | outcome.reserve_ids
    for candidate in outcome.eligible:
        is_selected = candidate.id in selected
        matches.append(
            ResourceMatch(
                resource_id=candidate.id,
                distance_meters=candidate.distance_meters,
                score=candidate.score_value if candidate.score is not None else None,
                readiness=candidate.readiness,
                selected=is_selected,
                excluded=False,
                exclusion_reason=None if is_selected else ExclusionReason.NOT_SELECTED,
                detail=None if is_selected else "Не включено в состав.",
            )
        )
    for ex in outcome.recommendation.excluded:
        matches.append(
            ResourceMatch(
                resource_id=ex.candidate.id,
                distance_meters=ex.candidate.distance_meters,
                score=None,
                readiness=ex.candidate.readiness,
                selected=False,
                excluded=True,
                exclusion_reason=ex.reason,
                detail=ex.detail,
            )
        )
    return matches


# --------------------------------------------------------------- ORM → schema
def recommendation_to_response(
    orm: RecommendationORM,
    *,
    required_capabilities: list[CapabilityResponse] | None = None,
) -> RecommendationResponse:
    items = sorted(orm.items, key=lambda i: i.sort_order)
    reasons_by_item = _reasons_by_item(orm)
    primary = [
        _item_to_schema(i, reasons_by_item.get(i.id, []))
        for i in items
        if i.role is RecommendationRole.PRIMARY
    ]
    reserve = [
        _item_to_schema(i, reasons_by_item.get(i.id, []))
        for i in items
        if i.role is RecommendationRole.RESERVE
    ]
    global_reasons = [r.text for r in orm.reasons if r.item_id is None]

    return RecommendationResponse(
        id=orm.id,
        incident_id=orm.incident_id,
        incident_type_id=orm.incident_type_id,
        complexity=orm.complexity,
        point=DispatchPoint(latitude=orm.latitude, longitude=orm.longitude),
        address=orm.address,
        priority=orm.priority,
        status=orm.status,
        sufficient=orm.sufficient,
        confidence=orm.confidence,
        confidence_score=orm.confidence_score,
        total_candidates=orm.total_candidates,
        is_preview=orm.is_preview,
        required_capabilities=required_capabilities or [],
        primary_units=primary,
        reserve_units=reserve,
        capability_coverage=[
            CapabilityCoverageItem(
                code=c.capability_code,
                required=c.required_quantity,
                provided=c.provided_quantity,
                satisfied=c.satisfied,
                mandatory=c.mandatory,
            )
            for c in orm.capability_matches
        ],
        resource_matches=[
            ResourceMatchResponse(
                resource_id=m.resource_id,
                code=m.resource.code,
                name=m.resource.name,
                distance_meters=m.distance_meters,
                score=m.score,
                readiness=m.readiness,
                selected=m.selected,
                excluded=m.excluded,
                exclusion_reason=m.exclusion_reason,
                detail=m.detail,
            )
            for m in orm.resource_matches
        ],
        summary=_summary_to_schema(orm.summary) if orm.summary else None,
        messages=list(orm.summary.messages or []) if orm.summary else [],
        reasons=global_reasons,
        rule_codes=list(orm.decision.used_rule_codes or []) if orm.decision else [],
        created_at=orm.created_at,
    )


def _reasons_by_item(orm: RecommendationORM) -> dict[UUID, list[str]]:
    out: dict[UUID, list[str]] = {}
    for reason in orm.reasons:
        if reason.item_id is not None:
            out.setdefault(reason.item_id, []).append(reason.text)
    return out


def _item_to_schema(
    item: RecommendationItemORM, reasons: list[str]
) -> RecommendationItem:
    r = item.resource
    rt, org, st = r.resource_type, r.organization, r.availability_status
    caps = sorted(
        link.capability.code
        for link in r.capability_links
        if not link.is_deleted and link.capability is not None
    )
    return RecommendationItem(
        id=item.id,
        resource_id=item.resource_id,
        code=r.code,
        name=r.name,
        role=item.role,
        distance_meters=item.distance_meters,
        score=item.score,
        readiness=item.readiness,
        capabilities=caps,
        reasons=reasons,
        resource_type=_ref(rt),
        organization=_ref(org),
        availability_status=_ref(st),
    )


def _summary_to_schema(summary: RecommendationSummary) -> RecommendationSummaryResponse:
    return RecommendationSummaryResponse(
        primary_count=summary.primary_count,
        reserve_count=summary.reserve_count,
        minimum_units=summary.minimum_units,
        recommended_units=summary.recommended_units,
        reserve_units=summary.reserve_units,
        required_capabilities=list(summary.required_capabilities or []),
        covered_capabilities=list(summary.covered_capabilities or []),
        missing_capabilities=list(summary.missing_capabilities or []),
        messages=list(summary.messages or []),
    )


def recommendation_to_history_item(
    orm: RecommendationORM,
) -> RecommendationHistoryItem:
    primary_count = sum(
        1 for i in orm.items if i.role is RecommendationRole.PRIMARY
    )
    return RecommendationHistoryItem(
        id=orm.id,
        incident_id=orm.incident_id,
        incident_type_id=orm.incident_type_id,
        status=orm.status,
        confidence=orm.confidence,
        sufficient=orm.sufficient,
        primary_count=primary_count,
        is_preview=orm.is_preview,
        created_at=orm.created_at,
    )


def _ref(row) -> RefLabel | None:
    if row is None:
        return None
    return RefLabel(id=row.id, code=row.code, name=row.name)
