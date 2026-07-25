"""Candidate retrieval for dispatch.

Reuses the Stage-4 SearchEngine / SearchRepository to fetch resources near the
incident (by resource category and radius), then batch-loads each candidate's
capabilities and service zones (coverage areas) in single queries — no N+1.

Availability, capability and service-zone *filtering* is deliberately **not**
done here: the engine applies it so every exclusion can be explained and logged.
An optional organization requirement is pushed down to the search for efficiency.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dispatch.algorithms.candidate import DispatchCandidate
from app.dispatch.utils.readiness import readiness_of
from app.models.catalog import Capability
from app.models.enums import ResourceCategory
from app.models.geo import CoverageArea
from app.models.resource import ResourceCapability
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
    OrganizationFilter,
    ResourceFilter,
    ResourceGroupFilter,
)
from app.search.repositories import SearchRepository


class CandidateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._engine = SearchEngine()
        self._search = SearchRepository(session)

    async def resolve_capability_labels(
        self, codes: Sequence[str]
    ) -> dict[str, str]:
        if not codes:
            return {}
        rows = await self._session.execute(
            select(Capability.code, Capability.name).where(
                Capability.code.in_(list(codes))
            )
        )
        return {code: name for code, name in rows.all()}

    async def fetch_candidates(
        self,
        point: GeoPoint,
        *,
        categories: Sequence[ResourceCategory],
        radius_meters: float,
        limit: int,
        organization_ids: Sequence[UUID] = (),
    ) -> list[DispatchCandidate]:
        filters: list[ResourceFilter] = []
        if categories:
            filters.append(ResourceGroupFilter(list(categories)))
        if organization_ids:
            filters.append(OrganizationFilter(list(organization_ids)))

        criteria = SearchCriteria(
            filters=filters,
            spatial=SpatialConstraint(point=point, radius_meters=radius_meters),
            sort=[SortSpec(SortField.DISTANCE)],
            pagination=Pagination(limit=limit, offset=0),
        )
        result = await self._search.execute(self._engine.build(criteria))

        resource_ids = [c.resource.id for c in result.candidates]
        capabilities = await self._load_capabilities(resource_ids)
        service_areas = await self._load_service_areas(resource_ids)

        return [
            DispatchCandidate(
                resource=c.resource,
                distance_meters=c.distance_meters,
                readiness=readiness_of(c.resource),
                capabilities=capabilities.get(c.resource.id, {}),
                service_area_ids=service_areas.get(c.resource.id, set()),
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
                    ResourceCapability.resource_id.in_(list(resource_ids)),
                    ResourceCapability.is_deleted.is_(False),
                )
            )
        )
        out: dict[UUID, dict[str, int]] = {}
        for resource_id, code, quantity in rows.all():
            out.setdefault(resource_id, {})[code] = quantity
        return out

    async def _load_service_areas(
        self, resource_ids: Sequence[UUID]
    ) -> dict[UUID, set[UUID]]:
        if not resource_ids:
            return {}
        rows = await self._session.execute(
            select(CoverageArea.resource_id, CoverageArea.administrative_area_id).where(
                and_(
                    CoverageArea.resource_id.in_(list(resource_ids)),
                    CoverageArea.administrative_area_id.is_not(None),
                    CoverageArea.is_deleted.is_(False),
                )
            )
        )
        out: dict[UUID, set[UUID]] = {}
        for resource_id, area_id in rows.all():
            out.setdefault(resource_id, set()).add(area_id)
        return out
