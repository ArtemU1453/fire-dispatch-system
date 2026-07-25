"""Spatial service — PostGIS query primitives.

Thin application layer over :class:`SpatialRepository`. Provides the operations
Stage 3 must support (distance, radius, polygon, administrative area, bounding
box) that **prepare data for nearest-resource search** — without performing that
search, ranking, routing or ETA (explicitly out of scope for this stage).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.gis.repositories.spatial import SpatialRepository
from app.models.resource import Resource


class SpatialService:
    """Geospatial queries over resources (and other geom-bearing models)."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = SpatialRepository(session)

    async def distance_meters(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        return await self._repo.distance_meters(lat1, lon1, lat2, lon2)

    async def resources_within_radius(
        self,
        latitude: float,
        longitude: float,
        radius_meters: float,
        *,
        limit: int = 100,
    ) -> Sequence[Resource]:
        return await self._repo.within_radius(
            latitude, longitude, radius_meters, model=Resource, limit=limit
        )

    async def resources_within_polygon(
        self, polygon_wkt: str, *, limit: int = 100
    ) -> Sequence[Resource]:
        return await self._repo.within_polygon(polygon_wkt, model=Resource, limit=limit)

    async def resources_within_area(
        self, area_id: UUID, *, limit: int = 100
    ) -> Sequence[Resource]:
        return await self._repo.within_administrative_area(
            area_id, model=Resource, limit=limit
        )

    async def resources_within_bbox(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        *,
        limit: int = 100,
    ) -> Sequence[Any]:
        return await self._repo.within_bbox(
            min_lon, min_lat, max_lon, max_lat, model=Resource, limit=limit
        )
