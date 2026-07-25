"""Spatial repository — PostGIS-powered queries.

Encapsulates the raw spatial SQL so services stay declarative. Every method uses
PostGIS functions (``ST_DWithin``, ``ST_Distance``, ``ST_Within``,
``ST_MakeEnvelope``) and casts to ``geography`` where metric distance is needed,
so radius/distance are in metres on the WGS-84 sphere.

Queries default to the Stage-2 ``Resource`` (the dispatchable objects) but accept
any model exposing a ``geom`` column, so the same primitives serve buildings or
future spatial entities. **No dispatch logic here** — these only *return the
candidate set*; ranking / selection belongs to the next stage.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import Float, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.geo import AdministrativeArea
from app.models.mixins import SRID
from app.models.resource import Resource


def _point(latitude: float, longitude: float) -> Any:
    """Build a SRID-4326 point expression from lat/lon."""
    return func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), SRID)


class SpatialRepository:
    """PostGIS spatial queries over resources (and other geom-bearing models)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def distance_meters(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """Great-circle distance between two points, in metres."""
        stmt = select(
            cast(
                func.ST_Distance(
                    cast(_point(lat1, lon1), Geography),
                    cast(_point(lat2, lon2), Geography),
                ),
                Float,
            )
        )
        result = await self._session.execute(stmt)
        return float(result.scalar_one())

    async def within_radius(
        self,
        latitude: float,
        longitude: float,
        radius_meters: float,
        *,
        model: type = Resource,
        limit: int = 100,
    ) -> Sequence[Any]:
        """Objects whose point is within ``radius_meters`` of the centre.

        Ordered by ascending distance. Uses ``ST_DWithin`` on ``geography`` so
        the index is used and the radius is metric.
        """
        centre = _point(latitude, longitude)
        stmt = (
            select(model)
            .where(self._not_deleted(model))
            .where(model.geom.isnot(None))
            .where(
                func.ST_DWithin(
                    cast(model.geom, Geography),
                    cast(centre, Geography),
                    radius_meters,
                )
            )
            .order_by(
                func.ST_Distance(cast(model.geom, Geography), cast(centre, Geography))
            )
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def within_polygon(
        self,
        polygon_wkt: str,
        *,
        model: type = Resource,
        limit: int = 100,
    ) -> Sequence[Any]:
        """Objects whose point lies inside the given WKT polygon (SRID 4326)."""
        polygon = func.ST_SetSRID(func.ST_GeomFromText(polygon_wkt), SRID)
        stmt = (
            select(model)
            .where(self._not_deleted(model))
            .where(model.geom.isnot(None))
            .where(func.ST_Within(model.geom, polygon))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def within_administrative_area(
        self,
        area_id: UUID,
        *,
        model: type = Resource,
        limit: int = 100,
    ) -> Sequence[Any]:
        """Objects contained by a Stage-2 administrative area's boundary."""
        boundary = (
            select(AdministrativeArea.boundary)
            .where(AdministrativeArea.id == area_id)
            .scalar_subquery()
        )
        stmt = (
            select(model)
            .where(self._not_deleted(model))
            .where(model.geom.isnot(None))
            .where(func.ST_Within(model.geom, boundary))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def within_bbox(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        *,
        model: type = Resource,
        limit: int = 100,
    ) -> Sequence[Any]:
        """Objects whose point falls inside the bounding box (uses the GiST &&)."""
        envelope = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, SRID)
        stmt = (
            select(model)
            .where(self._not_deleted(model))
            .where(model.geom.isnot(None))
            .where(model.geom.op("&&")(envelope))
            .where(func.ST_Within(model.geom, envelope))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    def _not_deleted(model: type) -> Any:
        is_deleted = getattr(model, "is_deleted", None)
        if is_deleted is not None:
            return is_deleted.is_(False)
        return func.true()
