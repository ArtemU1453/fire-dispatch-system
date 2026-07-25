"""Mapping between routing domain objects and API schemas."""

from __future__ import annotations

from app.routing.models.domain import (
    DistanceResult,
    ETAResult,
    ProviderHealth,
    RoutePoint,
    RoutingResponse,
)
from app.routing.schemas.responses import (
    DistanceResponse,
    ETAResponse,
    HealthResponse,
    PointOutput,
    RouteResponse,
    SegmentOutput,
)


def _point(p: RoutePoint) -> PointOutput:
    return PointOutput(
        latitude=p.latitude, longitude=p.longitude,
        name=p.name, is_waypoint=p.is_waypoint,
    )


def routing_response_to_schema(response: RoutingResponse) -> RouteResponse:
    route = response.route
    return RouteResponse(
        origin=PointOutput(
            latitude=route.origin.latitude, longitude=route.origin.longitude,
            name="origin", is_waypoint=True,
        ),
        destination=PointOutput(
            latitude=route.destination.latitude,
            longitude=route.destination.longitude,
            name="destination", is_waypoint=True,
        ),
        distance_meters=round(route.distance_meters, 1),
        distance_km=round(route.distance_meters / 1000.0, 3),
        duration_seconds=round(route.duration_seconds, 1),
        eta_minutes=round(route.duration_seconds / 60.0, 2),
        provider=route.provider,
        profile=route.profile,
        is_fallback=route.is_fallback,
        response_time_ms=response.response_time_ms,
        waypoints=[_point(p) for p in route.waypoints],
        segments=[
            SegmentOutput(
                distance_meters=round(s.distance_meters, 1),
                duration_seconds=round(s.duration_seconds, 1),
            )
            for s in route.segments
        ],
        geometry=[_point(p) for p in route.geometry],
    )


def eta_to_schema(result: ETAResult) -> ETAResponse:
    return ETAResponse(
        origin=PointOutput(
            latitude=result.origin.latitude, longitude=result.origin.longitude
        ),
        destination=PointOutput(
            latitude=result.destination.latitude,
            longitude=result.destination.longitude,
        ),
        eta_seconds=round(result.eta_seconds, 1),
        eta_minutes=result.eta_minutes,
        distance_meters=round(result.distance_meters, 1),
        provider=result.provider,
        is_fallback=result.is_fallback,
    )


def distance_to_schema(result: DistanceResult) -> DistanceResponse:
    return DistanceResponse(
        origin=PointOutput(
            latitude=result.origin.latitude, longitude=result.origin.longitude
        ),
        destination=PointOutput(
            latitude=result.destination.latitude,
            longitude=result.destination.longitude,
        ),
        distance_meters=round(result.distance_meters, 1),
        distance_km=result.distance_km,
        provider=result.provider,
        is_fallback=result.is_fallback,
    )


def health_to_schema(health: ProviderHealth) -> HealthResponse:
    return HealthResponse(
        provider=health.provider,
        healthy=health.healthy,
        detail=health.detail,
        latency_ms=health.latency_ms,
    )
