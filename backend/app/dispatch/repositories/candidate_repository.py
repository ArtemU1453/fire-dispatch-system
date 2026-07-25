"""Candidate retrieval for dispatch.

Reuses the Stage-4 SearchEngine/SearchRepository to fetch available resources
near the incident (honouring the rule's categories, radius, capability and
exclusion filters), then batch-loads each candidate's capabilities in a single
query — no N+1. Resolving capability/status *codes* (from the rules) to ids is
also done here.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import Select, and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dispatch.algorithms.candidate import DispatchCandidate
from app.dispatch.rules.models import IncidentRule
from app.dispatch.utils.readiness import readiness_of
from app.models.catalog import AvailabilityStatus, Capability
from app.models.resource import Resource, ResourceCapability
from app.search.criteria import (
    GeoPoint,
    Pagination,
    SearchCriteria,
    SortField,
    SortSpec,
    SpatialConstraint,
)
from app.search.engine import SearchEngine
from app.search.filters import (
    CapabilityFilter,
    ResourceFilter,
    ResourceGroupFilter,
    WorkingStatusFilter,
)
from app.search.repositories import SearchRepository


class _ExcludeStatusFilter(ResourceFilter):
    """Excludes resources whose availability status is in the excluded set."""

    def __init__(self, status_ids: Sequence[UUID]) -> None:
        self._ids = list(status_ids)

    def is_active(self) -> bool:
        return bool(self._ids)

    def apply(self, stmt: Select) -> Select:
        if not self._ids:
            return stmt
        return stmt.where(
            (Resource.availability_status_id.is_(None))
            | (Resource.availability_status_id.notin_(self._ids))
        )


class CandidateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._engine = SearchEngine()
        self._search = SearchRepository(session)

    async def resolve_capability_ids(
        self, codes: Sequence[str]
    ) -> dict[str, UUID]:
        if not codes:
            return {}
        rows = await self._session.execute(
            select(Capability.code, Capability.id).where(Capability.code.in_(codes))
        )
        return {code: cid for code, cid in rows.all()}

    async def resolve_status_ids(self, codes: Sequence[str]) -> list[UUID]:
        if not codes:
            return []
        rows = await self._session.execute(
            select(AvailabilityStatus.id).where(AvailabilityStatus.code.in_(codes))
        )
        return [r for (r,) in rows.all()]

    async def fetch_candidates(
        self, point: GeoPoint, rule: IncidentRule, exclusions
    ) -> list[DispatchCandidate]:
        required_codes = [c.code for c in rule.required_capabilities]
        cap_ids_by_code = await self.resolve_capability_ids(required_codes)
        excluded_status_ids = await self.resolve_status_ids(
            exclusions.excluded_status_codes
        )

        filters: list[ResourceFilter] = [
            ResourceGroupFilter(rule.resource_categories),
            WorkingStatusFilter(
                is_active=True if exclusions.require_active else None,
                operational=True if exclusions.require_operational else None,
                deployable=True if exclusions.require_deployable else None,
            ),
            _ExcludeStatusFilter(excluded_status_ids),
        ]
        if cap_ids_by_code:
            filters.append(
                CapabilityFilter(list(cap_ids_by_code.values()), match_all=False)
            )

        criteria = SearchCriteria(
            filters=filters,
            spatial=SpatialConstraint(
                point=point, radius_meters=rule.search_radius_meters
            ),
            sort=[SortSpec(SortField.DISTANCE)],
            pagination=Pagination(limit=rule.candidate_limit, offset=0),
        )
        result = await self._search.execute(self._engine.build(criteria))

        resource_ids = [c.resource.id for c in result.candidates]
        capabilities = await self._load_capabilities(resource_ids)

        return [
            DispatchCandidate(
                resource=c.resource,
                distance_meters=c.distance_meters,
                readiness=readiness_of(c.resource),
                capabilities=capabilities.get(c.resource.id, {}),
            )
            for c in result.candidates
        ]

    async def _load_capabilities(
        self, resource_ids: Sequence[UUID]
    ) -> dict[UUID, dict[str, int]]:
        if not resource_ids:
            return {}
        rows = await self._session.execute(
            select(
                ResourceCapability.resource_id,
                Capability.code,
                ResourceCapability.quantity,
            )
            .join(Capability, Capability.id == ResourceCapability.capability_id)
            .where(
                and_(
                    ResourceCapability.resource_id.in_(resource_ids),
                    ResourceCapability.is_deleted.is_(False),
                )
            )
        )
        out: dict[UUID, dict[str, int]] = {}
        for resource_id, code, quantity in rows.all():
            out.setdefault(resource_id, {})[code] = quantity
        return out
