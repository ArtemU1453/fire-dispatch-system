"""Dispatch response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.dispatch.models.enums import (
    ConfidenceLevel,
    DispatchStatus,
    ExclusionReason,
    RecommendationRole,
)
from app.rules.models.enums import IncidentComplexity, RulePriority
from app.schemas.common import SchemaBase


class RefLabel(SchemaBase):
    id: UUID
    code: str | None = None
    name: str | None = None


class CapabilityResponse(SchemaBase):
    """A capability an incident requires (consolidated from the rules)."""

    code: str
    min_quantity: int
    mandatory: bool
    label: str | None = None


class CapabilityCoverageItem(SchemaBase):
    """How a required capability is covered by the recommended units."""

    code: str
    label: str | None = None
    required: int
    provided: int
    satisfied: bool
    mandatory: bool


class RecommendationItem(SchemaBase):
    """A recommended (primary or reserve) unit with rationale."""

    id: UUID
    resource_id: UUID
    code: str
    name: str
    role: RecommendationRole
    distance_meters: float | None = None
    score: float | None = None
    readiness: str
    capabilities: list[str] = []
    reasons: list[str] = []
    resource_type: RefLabel | None = None
    organization: RefLabel | None = None
    availability_status: RefLabel | None = None


class ResourceMatchResponse(SchemaBase):
    """A considered resource — selected or excluded (with reason)."""

    resource_id: UUID
    code: str
    name: str
    distance_meters: float | None = None
    score: float | None = None
    readiness: str
    selected: bool
    excluded: bool
    exclusion_reason: ExclusionReason | None = None
    detail: str | None = None


class RecommendationSummaryResponse(SchemaBase):
    """Roll-up figures for a recommendation."""

    primary_count: int
    reserve_count: int
    minimum_units: int
    recommended_units: int
    reserve_units: int
    required_capabilities: list[str] = []
    covered_capabilities: list[str] = []
    missing_capabilities: list[str] = []
    messages: list[str] = []


class DispatchPoint(SchemaBase):
    latitude: float
    longitude: float


class RecommendationResponse(SchemaBase):
    """The full advisory recommendation (as produced and as persisted)."""

    id: UUID
    incident_id: UUID | None = None
    incident_type_id: UUID
    complexity: IncidentComplexity | None = None
    point: DispatchPoint
    address: str | None = None
    priority: RulePriority
    status: DispatchStatus
    sufficient: bool
    confidence: ConfidenceLevel
    confidence_score: float
    total_candidates: int
    is_preview: bool
    required_capabilities: list[CapabilityResponse] = []
    primary_units: list[RecommendationItem] = []
    reserve_units: list[RecommendationItem] = []
    capability_coverage: list[CapabilityCoverageItem] = []
    resource_matches: list[ResourceMatchResponse] = []
    summary: RecommendationSummaryResponse | None = None
    messages: list[str] = []
    reasons: list[str] = []
    rule_codes: list[str] = []
    created_at: datetime | None = None


class DispatchResponse(SchemaBase):
    """Top-level response envelope for POST /dispatch/recommend and /preview."""

    recommendation: RecommendationResponse


class RecommendationHistoryItem(SchemaBase):
    """A compact entry for a recommendation-history listing."""

    id: UUID
    incident_id: UUID | None = None
    incident_type_id: UUID
    status: DispatchStatus
    confidence: ConfidenceLevel
    sufficient: bool
    primary_count: int
    is_preview: bool
    created_at: datetime | None = None
