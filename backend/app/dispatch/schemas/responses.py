"""Dispatch response schemas."""

from __future__ import annotations

from uuid import UUID

from app.models.enums import ResourceCategory
from app.schemas.common import SchemaBase


class RefLabel(SchemaBase):
    id: UUID
    code: str | None = None
    name: str | None = None


class CapabilityRequirement(SchemaBase):
    """A capability an incident type requires."""

    code: str
    min_quantity: int
    label: str | None = None


class CapabilityCoverageItem(SchemaBase):
    """How a required capability is covered by the recommended units."""

    code: str
    label: str | None = None
    required: int
    provided: int
    satisfied: bool


class RecommendationItem(SchemaBase):
    """A single recommended (or reserve) unit with rationale."""

    id: UUID
    code: str
    name: str
    role: str
    distance_meters: float | None = None
    score: float | None = None
    readiness: str
    capabilities: list[str] = []
    reasons: list[str] = []
    resource_type: RefLabel | None = None
    organization: RefLabel | None = None
    availability_status: RefLabel | None = None


class Recommendation(SchemaBase):
    """The advisory composition for the dispatcher."""

    sufficient: bool
    confidence: str
    confidence_score: float
    primary_units: list[RecommendationItem]
    reserve_units: list[RecommendationItem]
    capability_coverage: list[CapabilityCoverageItem]
    messages: list[str]
    is_preview: bool = False


class DispatchPoint(SchemaBase):
    latitude: float
    longitude: float


class DispatchResponse(SchemaBase):
    """Top-level recommendation response."""

    incident_type: str
    incident_name: str
    priority: int
    point: DispatchPoint
    total_candidates: int
    recommendation: Recommendation


class RuleResponse(SchemaBase):
    """A read view of one incident rule (for GET /dispatch/rules)."""

    code: str
    name: str
    priority: int
    resource_categories: list[ResourceCategory]
    required_capabilities: list[CapabilityRequirement]
    minimum_units: int
    recommended_units: int
    reserve_units: int
    search_radius_meters: float


class CapabilityInfo(SchemaBase):
    """A capability from the catalog (for GET /dispatch/capabilities)."""

    id: UUID
    code: str
    name: str
    description: str | None = None
