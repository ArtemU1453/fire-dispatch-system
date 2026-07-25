"""Resource search REST endpoints.

Thin adapters over :class:`SearchService`. Rich filters arrive as query
parameters, assembled into request schemas by shared dependencies so
``/search`` and ``/filter`` stay DRY.

    GET /resources/search    — full combinable search (filters + spatial + sort)
    GET /resources/nearest   — nearest resources to a point / address
    GET /resources/radius    — resources within a radius
    GET /resources/filter    — attribute-only filtering (no spatial reference)
    GET /resources/{id}      — a single resource
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.enums import ResourceCategory
from app.search.criteria import SortDirection, SortField
from app.search.deps import SearchServiceDep
from app.search.schemas.requests import (
    FilterRequest,
    NearestRequest,
    PaginationRequest,
    RadiusRequest,
    SearchRequest,
    SortItem,
    SpatialRequest,
)
from app.search.schemas.responses import ResourceSearchItem, SearchResponse

router = APIRouter(prefix="/resources", tags=["resource-search"])


# --------------------------------------------------------------- shared deps
def filter_params(
    ids: list[UUID] = Query(default=[]),
    resource_type_ids: list[UUID] = Query(default=[]),
    categories: list[ResourceCategory] = Query(default=[]),
    organization_ids: list[UUID] = Query(default=[]),
    availability_status_ids: list[UUID] = Query(default=[]),
    capability_ids: list[UUID] = Query(default=[]),
    capability_match_all: bool = Query(default=False),
    station_ids: list[UUID] = Query(default=[]),
    vehicle_type_ids: list[UUID] = Query(default=[]),
    equipment_type_ids: list[UUID] = Query(default=[]),
    is_active: bool | None = Query(default=None),
    operational: bool | None = Query(default=None),
    deployable: bool | None = Query(default=None),
    q: str | None = Query(default=None, description="Partial name match."),
    code: str | None = Query(default=None),
    address_contains: str | None = Query(default=None),
) -> FilterRequest:
    return FilterRequest(
        ids=ids,
        resource_type_ids=resource_type_ids,
        categories=categories,
        organization_ids=organization_ids,
        availability_status_ids=availability_status_ids,
        capability_ids=capability_ids,
        capability_match_all=capability_match_all,
        station_ids=station_ids,
        vehicle_type_ids=vehicle_type_ids,
        equipment_type_ids=equipment_type_ids,
        is_active=is_active,
        operational=operational,
        deployable=deployable,
        name_contains=q,
        code=code,
        address_contains=address_contains,
    )


FilterDep = Annotated[FilterRequest, Depends(filter_params)]


def _parse_sort(tokens: list[str]) -> list[SortItem]:
    items: list[SortItem] = []
    for token in tokens:
        descending = token.startswith("-")
        name = token[1:] if descending else token
        try:
            field = SortField(name)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unknown sort field: {name!r}",
            ) from exc
        items.append(
            SortItem(
                field=field,
                direction=SortDirection.DESC if descending else SortDirection.ASC,
            )
        )
    return items


def _parse_bbox(bbox: str | None) -> tuple[float, float, float, float] | None:
    if not bbox:
        return None
    try:
        parts = tuple(float(p) for p in bbox.split(","))
    except ValueError as exc:
        raise HTTPException(422, detail="bbox needs 4 comma-separated floats") from exc
    if len(parts) != 4:
        raise HTTPException(422, detail="bbox = 'min_lon,min_lat,max_lon,max_lat'")
    return parts  # type: ignore[return-value]


# ------------------------------------------------------------------- routes
@router.get("/search", response_model=SearchResponse, summary="Universal search")
async def search(
    service: SearchServiceDep,
    filters: FilterDep,
    lat: float | None = Query(default=None, ge=-90, le=90),
    lon: float | None = Query(default=None, ge=-180, le=180),
    radius_m: float | None = Query(default=None, gt=0, le=1_000_000),
    area_id: UUID | None = Query(default=None),
    polygon_wkt: str | None = Query(default=None),
    bbox: str | None = Query(default=None, description="bbox as 4 floats"),
    address: str | None = Query(default=None, description="Geocoded to a point."),
    sort: list[str] = Query(default=[], description="e.g. sort=distance&sort=-name"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> SearchResponse:
    request = SearchRequest(
        filters=filters,
        spatial=SpatialRequest(
            latitude=lat,
            longitude=lon,
            radius_meters=radius_m,
            area_id=area_id,
            polygon_wkt=polygon_wkt,
            bbox=_parse_bbox(bbox),
            address=address,
        ),
        sort=_parse_sort(sort),
        pagination=PaginationRequest(limit=limit, offset=offset),
    )
    return await service.search(request)


@router.get("/nearest", response_model=SearchResponse, summary="Nearest resources")
async def nearest(
    service: SearchServiceDep,
    filters: FilterDep,
    lat: float | None = Query(default=None, ge=-90, le=90),
    lon: float | None = Query(default=None, ge=-180, le=180),
    address: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=500),
) -> SearchResponse:
    if lat is None and lon is None and not address:
        raise HTTPException(422, detail="Provide lat/lon or address")
    return await service.nearest(
        NearestRequest(
            latitude=lat, longitude=lon, address=address, limit=limit, filters=filters
        )
    )


@router.get("/radius", response_model=SearchResponse, summary="Resources in radius")
async def radius(
    service: SearchServiceDep,
    filters: FilterDep,
    radius_m: float = Query(gt=0, le=1_000_000),
    lat: float | None = Query(default=None, ge=-90, le=90),
    lon: float | None = Query(default=None, ge=-180, le=180),
    address: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> SearchResponse:
    if lat is None and lon is None and not address:
        raise HTTPException(422, detail="Provide lat/lon or address")
    return await service.radius(
        RadiusRequest(
            latitude=lat,
            longitude=lon,
            address=address,
            radius_meters=radius_m,
            pagination=PaginationRequest(limit=limit, offset=offset),
            filters=filters,
        )
    )


@router.get("/filter", response_model=SearchResponse, summary="Attribute-only filter")
async def filter_resources(
    service: SearchServiceDep,
    filters: FilterDep,
    sort: list[str] = Query(default=[]),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> SearchResponse:
    request = SearchRequest(
        filters=filters,
        sort=_parse_sort(sort),
        pagination=PaginationRequest(limit=limit, offset=offset),
    )
    return await service.search(request)


@router.get("/{resource_id}", response_model=ResourceSearchItem, summary="One resource")
async def get_resource(
    service: SearchServiceDep,
    resource_id: UUID,
) -> ResourceSearchItem:
    item = await service.get_by_id(resource_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return item
