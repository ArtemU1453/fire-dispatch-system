"""Pydantic schemas for resource management."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from app.resources.models.enums import (
    AssignmentStatus,
    QualificationKind,
    ResourceEventType,
    TechnicalCondition,
)
from app.schemas.common import SchemaBase


class StatusRef(SchemaBase):
    """A status from the shared availability catalog."""

    id: UUID
    code: str
    name: str
    is_operational: bool
    is_available_for_dispatch: bool
    color: str | None = None


class RefLabel(SchemaBase):
    id: UUID
    code: str | None = None
    name: str | None = None


# ------------------------------------------------------------------ inputs ---
class StatusUpdateRequest(SchemaBase):
    """Change the status of a unit / vehicle / personnel."""

    status_code: str
    reason: str | None = None
    actor_name: str | None = None
    incident_id: UUID | None = None


class AssignCrewRequest(SchemaBase):
    crew_id: UUID
    actor_name: str | None = None


class CrewCompositionChange(SchemaBase):
    add_personnel_resource_ids: list[UUID] = []
    remove_personnel_resource_ids: list[UUID] = []
    actor_name: str | None = None


class AssignIncidentRequest(SchemaBase):
    incident_id: UUID
    role: str = "primary"
    actor_name: str | None = None


class BulkStatusUpdateRequest(SchemaBase):
    resource_ids: list[UUID]
    status_code: str
    reason: str | None = None
    actor_name: str | None = None


# --------------------------------------------------------------- responses ---
class CrewMemberResponse(SchemaBase):
    id: UUID
    personnel_resource_id: UUID
    name: str | None = None
    position: str | None = None
    is_commander: bool


class CrewResponse(SchemaBase):
    id: UUID
    code: str
    name: str
    unit_id: UUID | None = None
    shift: RefLabel | None = None
    is_on_duty: bool
    is_active: bool
    member_count: int
    members: list[CrewMemberResponse] = []


class UnitResponse(SchemaBase):
    id: UUID
    code: str
    name: str
    call_sign: str | None = None
    station_id: UUID | None = None
    organization: RefLabel | None = None
    vehicle_resource_id: UUID | None = None
    status: StatusRef | None = None
    is_active: bool
    is_available: bool
    crew_count: int
    active_assignment_id: UUID | None = None
    notes: str | None = None


class VehicleResponse(SchemaBase):
    resource_id: UUID
    code: str
    name: str
    plate_number: str | None = None
    vehicle_type: RefLabel | None = None
    organization: RefLabel | None = None
    status: StatusRef | None = None
    is_available: bool
    fuel_level_percent: int | None = None
    mileage_km: int | None = None
    technical_condition: TechnicalCondition | None = None
    last_service_at: datetime | None = None


class QualificationResponse(SchemaBase):
    code: str
    name: str
    kind: QualificationKind
    valid_until: date | None = None


class PersonnelResponse(SchemaBase):
    resource_id: UUID
    code: str
    full_name: str
    rank: str | None = None
    role: RefLabel | None = None
    status: StatusRef | None = None
    qualifications: list[QualificationResponse] = []


class AssignmentResponse(SchemaBase):
    id: UUID
    unit_id: UUID
    incident_id: UUID | None = None
    role: str
    status: AssignmentStatus
    assigned_at: datetime
    released_at: datetime | None = None


class StatusOverviewItem(SchemaBase):
    status: StatusRef
    resource_count: int


class HistoryEntryResponse(SchemaBase):
    id: UUID
    resource_id: UUID | None = None
    unit_id: UUID | None = None
    crew_id: UUID | None = None
    event_type: ResourceEventType
    from_value: str | None = None
    to_value: str | None = None
    source: str
    incident_id: UUID | None = None
    changed_by_name: str | None = None
    occurred_at: datetime
