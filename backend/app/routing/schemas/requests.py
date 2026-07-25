"""Routing request schemas."""

from __future__ import annotations

from pydantic import Field

from app.routing.models.domain import GeoPoint, TravelProfile
from app.schemas.common import SchemaBase


class PointInput(SchemaBase):
    """A WGS84 coordinate."""

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    def to_domain(self) -> GeoPoint:
        return GeoPoint(latitude=self.latitude, longitude=self.longitude)


class RouteRequest(SchemaBase):
    """A request to build a full route."""

    origin: PointInput
    destination: PointInput
    profile: TravelProfile = TravelProfile.DRIVING
    alternatives: bool = False


class ETARequest(SchemaBase):
    """A request for an estimated time of arrival."""

    origin: PointInput
    destination: PointInput
    profile: TravelProfile = TravelProfile.DRIVING


class DistanceRequest(SchemaBase):
    """A request for a travel distance."""

    origin: PointInput
    destination: PointInput
    profile: TravelProfile = TravelProfile.DRIVING
