"""SearchService — the orchestration entry point.

Combines GIS (address → point), the filter set, the SearchEngine and the
SearchRepository, applies the (pluggable) selection strategy, maps to response
schemas and optionally caches the result. Everything downstream — including the
next stage's automatic selection — reuses this service unchanged.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.gis.cache.base import GeoCache
from app.gis.services.geocoding import GeocodingService
from app.search.algorithms.selection import IdentitySelection, SelectionStrategy
from app.search.criteria import (
    GeoPoint,
    Pagination,
    SearchCriteria,
    SortField,
    SortSpec,
    SpatialConstraint,
)
from app.search.engine import SearchEngine
from app.search.filters import IdFilter
from app.search.repositories import SearchRepository
from app.search.schemas.requests import (
    NearestRequest,
    PaginationRequest,
    RadiusRequest,
    SearchRequest,
    SortItem,
    SpatialRequest,
)
from app.search.schemas.responses import (
    GeoPointOut,
    ResourceSearchItem,
    SearchResponse,
)
from app.search.utils.mapping import build_filters, cache_key, to_item

logger = get_logger(__name__)


class SearchService:
    """Universal resource search over the ``Resource`` entity."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        engine: SearchEngine | None = None,
        geocoding: GeocodingService | None = None,
        cache: GeoCache | None = None,
        selection: SelectionStrategy | None = None,
    ) -> None:
        self._engine = engine or SearchEngine()
        self._repo = SearchRepository(session)
        self._geocoding = geocoding
        self._cache = cache
        self._selection = selection or IdentitySelection()

    # --------------------------------------------------------------- search
    async def search(self, request: SearchRequest) -> SearchResponse:
        constraint, reference = await self._resolve_spatial(request.spatial)
        key = cache_key(request, reference=reference)

        if self._cache is not None:
            cached = await self._cache.get(key)
            if cached is not None:
                response = SearchResponse(**cached)
                response.from_cache = True
                return response

        criteria = SearchCriteria(
            filters=build_filters(request.filters),
            spatial=constraint,
            sort=[SortSpec(s.field, s.direction) for s in request.sort],
            pagination=Pagination(
                limit=request.pagination.limit, offset=request.pagination.offset
            ),
        )
        result = await self._repo.execute(self._engine.build(criteria))
        candidates = self._selection.apply(result.candidates)
        items = [to_item(c) for c in candidates]

        response = SearchResponse(
            total=result.total,
            limit=criteria.pagination.limit,
            offset=criteria.pagination.offset,
            count=len(items),
            reference_point=(
                GeoPointOut(latitude=reference[0], longitude=reference[1])
                if reference is not None
                else None
            ),
            items=items,
        )
        if self._cache is not None:
            await self._cache.set(key, response.model_dump(mode="json"))
        return response

    # ------------------------------------------------------------- by id
    async def get_by_id(self, resource_id: UUID) -> ResourceSearchItem | None:
        criteria = SearchCriteria(
            filters=[IdFilter([resource_id])], pagination=Pagination(limit=1)
        )
        result = await self._repo.execute(self._engine.build(criteria))
        if not result.candidates:
            return None
        return to_item(result.candidates[0])

    # ------------------------------------------------------------- nearest
    async def nearest(self, request: NearestRequest) -> SearchResponse:
        return await self.search(
            SearchRequest(
                filters=request.filters,
                spatial=SpatialRequest(
                    latitude=request.latitude,
                    longitude=request.longitude,
                    address=request.address,
                ),
                sort=[SortItem(field=SortField.DISTANCE)],
                pagination=PaginationRequest(limit=request.limit, offset=0),
            )
        )

    # -------------------------------------------------------------- radius
    async def radius(self, request: RadiusRequest) -> SearchResponse:
        return await self.search(
            SearchRequest(
                filters=request.filters,
                spatial=SpatialRequest(
                    latitude=request.latitude,
                    longitude=request.longitude,
                    address=request.address,
                    radius_meters=request.radius_meters,
                ),
                sort=[SortItem(field=SortField.DISTANCE)],
                pagination=request.pagination,
            )
        )

    # ------------------------------------------------------------- helpers
    async def _resolve_spatial(
        self, sp: SpatialRequest
    ) -> tuple[SpatialConstraint, tuple[float, float] | None]:
        point: GeoPoint | None = None
        reference: tuple[float, float] | None = None
        if sp.latitude is not None and sp.longitude is not None:
            point = GeoPoint(sp.latitude, sp.longitude)
            reference = (sp.latitude, sp.longitude)
        elif sp.address and self._geocoding is not None:
            outcome = await self._geocoding.geocode(sp.address, limit=1)
            if outcome.results:
                best = outcome.results[0]
                point = GeoPoint(best.latitude, best.longitude)
                reference = (best.latitude, best.longitude)
        constraint = SpatialConstraint(
            point=point,
            radius_meters=sp.radius_meters,
            polygon_wkt=sp.polygon_wkt,
            area_id=sp.area_id,
            bbox=tuple(sp.bbox) if sp.bbox is not None else None,
        )
        return constraint, reference
