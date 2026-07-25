"""Dispatch request schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from app.rules.models.enums import IncidentComplexity
from app.schemas.common import SchemaBase


class DispatchConstraints(SchemaBase):
    """Manual constraints a dispatcher may impose on the recommendation."""

    organization_ids: list[UUID] = Field(
        default_factory=list,
        description="Restrict candidates to these organizations.",
    )
    excluded_resource_ids: list[UUID] = Field(
        default_factory=list, description="Resources to exclude explicitly."
    )
    radius_meters: float | None = Field(
        default=None, gt=0, le=200000, description="Override the search radius."
    )
    time_of_day_hour: int | None = Field(
        default=None, ge=0, le=23, description="Hour of day for time-based rules."
    )


class DispatchRequest(SchemaBase):
    """Incident parameters for a recommendation.

    Provide ``latitude``/``longitude`` or an ``address`` (geocoded to a point).
    """

    incident_id: UUID | None = Field(
        default=None, description="External incident identifier (for history)."
    )
    incident_type_id: UUID = Field(description="Incident type (catalog) id.")
    complexity: IncidentComplexity | None = Field(
        default=None, description="Incident complexity/category."
    )
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    address: str | None = Field(default=None, description="Geocoded if no coords.")
    administrative_area_id: UUID | None = Field(
        default=None, description="Administrative territory of the incident."
    )
    danger_level: str | None = Field(
        default=None, description="Danger level (e.g. low/elevated/high/critical)."
    )
    object_type: str | None = Field(
        default=None, description="Type of the object involved (school, hospital, …)."
    )
    flags: list[str] = Field(
        default_factory=list, description="Additional incident markers."
    )
    constraints: DispatchConstraints = Field(default_factory=DispatchConstraints)
