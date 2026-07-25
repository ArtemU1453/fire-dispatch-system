"""Dispatch request schemas."""

from __future__ import annotations

from pydantic import Field

from app.schemas.common import SchemaBase


class DispatchRequest(SchemaBase):
    """Incident parameters for a recommendation.

    Provide ``latitude``/``longitude`` or an ``address`` (geocoded to a point).
    """

    incident_type: str = Field(description="Incident type code, e.g. 'fire'.")
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    address: str | None = Field(default=None, description="Geocoded if no coords.")
    complexity: str | None = Field(
        default=None, description="Incident complexity/category (advisory)."
    )
    flags: list[str] = Field(
        default_factory=list, description="Additional incident markers."
    )
