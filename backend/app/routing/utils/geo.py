"""Geospatial helpers for routing (great-circle math — no traffic, no roads)."""

from __future__ import annotations

import math

from app.routing.models.domain import GeoPoint

EARTH_RADIUS_METERS = 6_371_000.0


def haversine_meters(origin: GeoPoint, destination: GeoPoint) -> float:
    """Great-circle distance between two points, in meters."""
    lat1 = math.radians(origin.latitude)
    lat2 = math.radians(destination.latitude)
    dlat = lat2 - lat1
    dlon = math.radians(destination.longitude - origin.longitude)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_METERS * math.asin(min(1.0, math.sqrt(a)))
