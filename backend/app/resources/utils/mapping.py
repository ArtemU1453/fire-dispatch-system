"""Mapping between resource-management ORM objects and API schemas."""

from __future__ import annotations

from app.models.catalog import AvailabilityStatus
from app.models.resource import Resource
from app.resources.models.entities import (
    Crew,
    CrewMember,
    PersonnelQualification,
    ResourceAssignment,
    ResourceManagementHistory,
    Unit,
    VehicleState,
)
from app.resources.models.enums import AssignmentStatus
from app.resources.schemas.resource import (
    AssignmentResponse,
    CrewMemberResponse,
    CrewResponse,
    HistoryEntryResponse,
    PersonnelResponse,
    QualificationResponse,
    RefLabel,
    StatusOverviewItem,
    StatusRef,
    UnitResponse,
    VehicleResponse,
)


def status_ref(status: AvailabilityStatus | None) -> StatusRef | None:
    if status is None:
        return None
    return StatusRef(
        id=status.id,
        code=status.code,
        name=status.name,
        is_operational=status.is_operational,
        is_available_for_dispatch=status.is_available_for_dispatch,
        color=status.color,
    )


def _ref(row) -> RefLabel | None:
    if row is None:
        return None
    return RefLabel(id=row.id, code=getattr(row, "code", None), name=row.name)


def unit_to_response(unit: Unit) -> UnitResponse:
    status = unit.availability_status
    active = next(
        (
            a
            for a in unit.assignments
            if a.status is AssignmentStatus.ACTIVE and not a.is_deleted
        ),
        None,
    )
    return UnitResponse(
        id=unit.id,
        code=unit.code,
        name=unit.name,
        call_sign=unit.call_sign,
        station_id=unit.station_id,
        organization=_ref(unit.organization),
        vehicle_resource_id=unit.vehicle_resource_id,
        status=status_ref(status),
        is_active=unit.is_active,
        is_available=bool(status and status.is_available_for_dispatch),
        crew_count=sum(1 for c in unit.crews if not c.is_deleted),
        active_assignment_id=active.id if active else None,
        notes=unit.notes,
    )


def vehicle_to_response(
    resource: Resource, state: VehicleState | None
) -> VehicleResponse:
    vehicle = resource.vehicle
    return VehicleResponse(
        resource_id=resource.id,
        code=resource.code,
        name=resource.name,
        plate_number=vehicle.plate_number if vehicle else None,
        vehicle_type=_ref(vehicle.vehicle_type) if vehicle else None,
        organization=_ref(resource.organization),
        status=status_ref(resource.availability_status),
        is_available=state.is_available if state else True,
        fuel_level_percent=state.fuel_level_percent if state else None,
        mileage_km=(
            state.mileage_km
            if state and state.mileage_km is not None
            else (vehicle.odometer_km if vehicle else None)
        ),
        technical_condition=state.technical_condition if state else None,
        last_service_at=state.last_service_at if state else None,
    )


def _member_to_response(member: CrewMember) -> CrewMemberResponse:
    return CrewMemberResponse(
        id=member.id,
        personnel_resource_id=member.personnel_resource_id,
        name=member.personnel.name if member.personnel else None,
        position=member.position,
        is_commander=member.is_commander,
    )


def crew_to_response(crew: Crew) -> CrewResponse:
    members = [m for m in crew.members if not m.is_deleted]
    return CrewResponse(
        id=crew.id,
        code=crew.code,
        name=crew.name,
        unit_id=crew.unit_id,
        shift=_ref(crew.shift),
        is_on_duty=crew.is_on_duty,
        is_active=crew.is_active,
        member_count=len(members),
        members=[_member_to_response(m) for m in members],
    )


def _full_name(resource: Resource) -> str:
    personnel = resource.personnel
    if personnel is None:
        return resource.name
    parts = [personnel.last_name, personnel.first_name, personnel.middle_name]
    name = " ".join(p for p in parts if p)
    return name or resource.name


def personnel_to_response(
    resource: Resource, qualifications: list[PersonnelQualification]
) -> PersonnelResponse:
    personnel = resource.personnel
    return PersonnelResponse(
        resource_id=resource.id,
        code=resource.code,
        full_name=_full_name(resource),
        rank=personnel.rank if personnel else None,
        role=_ref(personnel.role) if personnel and personnel.role else None,
        status=status_ref(resource.availability_status),
        qualifications=[
            QualificationResponse(
                code=q.code, name=q.name, kind=q.kind, valid_until=q.valid_until
            )
            for q in qualifications
            if not q.is_deleted
        ],
    )


def assignment_to_response(assignment: ResourceAssignment) -> AssignmentResponse:
    return AssignmentResponse(
        id=assignment.id,
        unit_id=assignment.unit_id,
        incident_id=assignment.incident_id,
        role=assignment.role,
        status=assignment.status,
        assigned_at=assignment.assigned_at,
        released_at=assignment.released_at,
    )


def overview_item(status: AvailabilityStatus, count: int) -> StatusOverviewItem:
    return StatusOverviewItem(status=status_ref(status), resource_count=count)


def history_to_response(entry: ResourceManagementHistory) -> HistoryEntryResponse:
    return HistoryEntryResponse(
        id=entry.id,
        resource_id=entry.resource_id,
        unit_id=entry.unit_id,
        crew_id=entry.crew_id,
        event_type=entry.event_type,
        from_value=entry.from_value,
        to_value=entry.to_value,
        source=entry.source,
        incident_id=entry.incident_id,
        changed_by_name=entry.changed_by_name,
        occurred_at=entry.occurred_at,
    )
