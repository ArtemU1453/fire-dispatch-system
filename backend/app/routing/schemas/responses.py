"""Routing response schemas."""

from __future__ import annotations

from app.routing.models.domain import TravelProfile
from app.schemas.common import SchemaBase


class PointOutput(SchemaBase):
    latitude: float
    longitude: float
    name: str | None = None
    is_waypoint: bool = False


class SegmentOutput(SchemaBase):
    distance_meters: float
    duration_seconds: float


class RouteResponse(SchemaBase):
    """A full route between two points."""

    origin: PointOutput
    destination: PointOutput
    distance_meters: float
    distance_km: float
    duration_seconds: float
    eta_minutes: float
    provider: str
    profile: TravelProfile
    is_fallback: bool
    response_time_ms: float
    waypoints: list[PointOutput] = []
    segments: list[SegmentOutput] = []
    geometry: list[PointOutput] = []


class ETAResponse(SchemaBase):
    """An estimated time of arrival."""

    origin: PointOutput
    destination: PointOutput
    eta_seconds: float
    eta_minutes: float
    distance_meters: float
    provider: str
    is_fallback: bool


class DistanceResponse(SchemaBase):
    """A travel distance."""

    origin: PointOutput
    destination: PointOutput
    distance_meters: float
    distance_km: float
    provider: str
    is_fallback: bool


class HealthResponse(SchemaBase):
    """Routing provider health."""

    provider: str
    healthy: bool
    detail: str | None = None
    latency_ms: float | None = None
