"""Spatial REST endpoints (PostGIS query primitives).

Expose the spatial operations required by Stage 3 (distance, radius, bounding
box, polygon, administrative area). They return *candidate sets* of geo-objects
(resources) — they do not rank or select for dispatch (next stage).
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query

from app.gis.deps import SpatialServiceDep
from app.gis.schemas.spatial import (
    DistanceResponse,
    SpatialObject,
    SpatialSearchResponse,
)

router = APIRouter(prefix="/spatial", tags=["gis-spatial"])


def _to_objects(rows) -> list[SpatialObject]:
    return [
        SpatialObject(
            id=r.id,
            code=getattr(r, "code", None),
            name=getattr(r, "name", None),
            latitude=getattr(r, "latitude", None),
            longitude=getattr(r, "longitude", None),
        )
        for r in rows
    ]


@router.get(
    "/distance",
    response_model=DistanceResponse,
    summary="Distance between two points",
)
async def distance(
    service: SpatialServiceDep,
    lat1: float = Query(ge=-90.0, le=90.0),
    lon1: float = Query(ge=-180.0, le=180.0),
    lat2: float = Query(ge=-90.0, le=90.0),
    lon2: float = Query(ge=-180.0, le=180.0),
) -> DistanceResponse:
    meters = await service.distance_meters(lat1, lon1, lat2, lon2)
    return DistanceResponse(distance_meters=meters)


@router.get(
    "/within-radius",
    response_model=SpatialSearchResponse,
    summary="Resources within a radius (metres)",
)
async def within_radius(
    service: SpatialServiceDep,
    lat: float = Query(ge=-90.0, le=90.0),
    lon: float = Query(ge=-180.0, le=180.0),
    radius_m: float = Query(gt=0, le=1_000_000),
    limit: int = Query(default=100, ge=1, le=1000),
) -> SpatialSearchResponse:
    rows = await service.resources_within_radius(lat, lon, radius_m, limit=limit)
    items = _to_objects(rows)
    return SpatialSearchResponse(count=len(items), items=items)


@router.get(
    "/within-bbox",
    response_model=SpatialSearchResponse,
    summary="Resources within a bounding box",
)
async def within_bbox(
    service: SpatialServiceDep,
    min_lon: float = Query(ge=-180.0, le=180.0),
    min_lat: float = Query(ge=-90.0, le=90.0),
    max_lon: float = Query(ge=-180.0, le=180.0),
    max_lat: float = Query(ge=-90.0, le=90.0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> SpatialSearchResponse:
    rows = await service.resources_within_bbox(
        min_lon, min_lat, max_lon, max_lat, limit=limit
    )
    items = _to_objects(rows)
    return SpatialSearchResponse(count=len(items), items=items)


@router.get(
    "/within-polygon",
    response_model=SpatialSearchResponse,
    summary="Resources within a WKT polygon (SRID 4326)",
)
async def within_polygon(
    service: SpatialServiceDep,
    wkt: str = Query(min_length=8, description="POLYGON((lon lat, ...)) in WGS-84."),
    limit: int = Query(default=100, ge=1, le=1000),
) -> SpatialSearchResponse:
    rows = await service.resources_within_polygon(wkt, limit=limit)
    items = _to_objects(rows)
    return SpatialSearchResponse(count=len(items), items=items)


@router.get(
    "/within-area/{area_id}",
    response_model=SpatialSearchResponse,
    summary="Resources within an administrative area's boundary",
)
async def within_area(
    service: SpatialServiceDep,
    area_id: UUID,
    limit: int = Query(default=100, ge=1, le=1000),
) -> SpatialSearchResponse:
    rows = await service.resources_within_area(area_id, limit=limit)
    items = _to_objects(rows)
    return SpatialSearchResponse(count=len(items), items=items)
