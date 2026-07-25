"""Routing REST endpoints.

    GET  /routing/route     — build a route between two points
    POST /routing/eta       — estimated time of arrival
    POST /routing/distance  — travel distance
    GET  /routing/health    — routing provider health

Provider outages return a clear 503 rather than crashing the caller.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.routing.deps import ETAServiceDep, RouteServiceDep
from app.routing.interfaces.routing_provider import (
    ProviderUnavailableError,
    RoutingError,
)
from app.routing.models.domain import GeoPoint, TravelProfile
from app.routing.schemas.requests import DistanceRequest, ETARequest
from app.routing.schemas.responses import (
    DistanceResponse,
    ETAResponse,
    HealthResponse,
    RouteResponse,
)
from app.routing.utils.mapping import (
    distance_to_schema,
    eta_to_schema,
    health_to_schema,
    routing_response_to_schema,
)

router = APIRouter(prefix="/routing", tags=["routing"])


def _unavailable(exc: ProviderUnavailableError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Routing provider unavailable: {exc}",
    )


def _bad_route(exc: RoutingError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
    )


@router.get("/route", response_model=RouteResponse, summary="Build a route")
async def build_route(
    service: RouteServiceDep,
    from_lat: float = Query(ge=-90, le=90),
    from_lon: float = Query(ge=-180, le=180),
    to_lat: float = Query(ge=-90, le=90),
    to_lon: float = Query(ge=-180, le=180),
    profile: TravelProfile = Query(default=TravelProfile.DRIVING),
    alternatives: bool = Query(default=False),
) -> RouteResponse:
    try:
        response = await service.build_route(
            GeoPoint(from_lat, from_lon),
            GeoPoint(to_lat, to_lon),
            profile=profile,
            alternatives=alternatives,
        )
    except ProviderUnavailableError as exc:
        raise _unavailable(exc) from exc
    except RoutingError as exc:
        raise _bad_route(exc) from exc
    return routing_response_to_schema(response)


@router.post("/eta", response_model=ETAResponse, summary="Estimate time of arrival")
async def estimate_eta(service: ETAServiceDep, request: ETARequest) -> ETAResponse:
    try:
        result = await service.estimate(
            request.origin.to_domain(),
            request.destination.to_domain(),
            profile=request.profile,
        )
    except ProviderUnavailableError as exc:
        raise _unavailable(exc) from exc
    except RoutingError as exc:
        raise _bad_route(exc) from exc
    return eta_to_schema(result)


@router.post(
    "/distance", response_model=DistanceResponse, summary="Compute travel distance"
)
async def compute_distance(
    service: RouteServiceDep, request: DistanceRequest
) -> DistanceResponse:
    try:
        result = await service.calculate_distance(
            request.origin.to_domain(),
            request.destination.to_domain(),
            profile=request.profile,
        )
    except ProviderUnavailableError as exc:
        raise _unavailable(exc) from exc
    except RoutingError as exc:
        raise _bad_route(exc) from exc
    return distance_to_schema(result)


@router.get("/health", response_model=HealthResponse, summary="Routing health")
async def health(service: RouteServiceDep) -> HealthResponse:
    return health_to_schema(await service.health())
