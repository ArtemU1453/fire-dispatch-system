"""Resource-management REST endpoints.

    GET   /units                     · GET /units/{id} · PATCH /units/{id}/status
    GET   /vehicles                  · GET /vehicles/{id} · PATCH /vehicles/{id}/status
    GET   /crews                     · GET /personnel
    GET   /resources/status          · GET /resources/history
    (+ integration: assign crew / incident, return, location, bulk status)

Statuses are stored in the database (the availability catalog) and change without
code; a change here updates the resource state the Dispatch Engine reads.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.resources.deps import ResourceServiceDep
from app.resources.models.enums import ResourceEventType
from app.resources.schemas.resource import (
    AssignCrewRequest,
    AssignIncidentRequest,
    BulkStatusUpdateRequest,
    CrewCompositionChange,
    CrewResponse,
    HistoryEntryResponse,
    PersonnelResponse,
    StatusOverviewItem,
    StatusUpdateRequest,
    UnitResponse,
    VehicleResponse,
)
from app.resources.tracking import Position
from app.resources.utils.mapping import (
    crew_to_response,
    history_to_response,
    overview_item,
    personnel_to_response,
    unit_to_response,
    vehicle_to_response,
)

router = APIRouter(tags=["resources"])


# ------------------------------------------------------------------- units ---
@router.get("/units", response_model=list[UnitResponse], summary="List units")
async def list_units(
    service: ResourceServiceDep,
    active_only: bool = Query(default=False),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[UnitResponse]:
    units = await service.list_units(
        active_only=active_only, limit=limit, offset=offset
    )
    return [unit_to_response(u) for u in units]


@router.get("/units/{unit_id}", response_model=UnitResponse, summary="Get unit")
async def get_unit(service: ResourceServiceDep, unit_id: UUID) -> UnitResponse:
    return unit_to_response(await service.get_unit(unit_id))


@router.patch(
    "/units/{unit_id}/status", response_model=UnitResponse,
    summary="Change unit status",
)
async def update_unit_status(
    service: ResourceServiceDep, unit_id: UUID, data: StatusUpdateRequest
) -> UnitResponse:
    unit = await service.update_unit_status(
        unit_id, data.status_code,
        actor_name=data.actor_name, reason=data.reason,
        incident_id=data.incident_id,
    )
    return unit_to_response(unit)


@router.post(
    "/units/{unit_id}/crew", response_model=UnitResponse, summary="Assign a crew"
)
async def assign_crew(
    service: ResourceServiceDep, unit_id: UUID, data: AssignCrewRequest
) -> UnitResponse:
    unit = await service.assign_crew(
        unit_id, data.crew_id, actor_name=data.actor_name
    )
    return unit_to_response(unit)


@router.post(
    "/units/{unit_id}/assign", response_model=UnitResponse,
    summary="Assign the unit to an incident",
)
async def assign_incident(
    service: ResourceServiceDep, unit_id: UUID, data: AssignIncidentRequest
) -> UnitResponse:
    unit = await service.assign_to_incident(
        unit_id, data.incident_id, role=data.role, actor_name=data.actor_name
    )
    return unit_to_response(unit)


@router.post(
    "/units/{unit_id}/return", response_model=UnitResponse,
    summary="Return the unit from the incident",
)
async def return_unit(
    service: ResourceServiceDep, unit_id: UUID, actor_name: str | None = None
) -> UnitResponse:
    unit = await service.return_from_incident(unit_id, actor_name=actor_name)
    return unit_to_response(unit)


@router.get("/units/{unit_id}/location", summary="Current unit location")
async def unit_location(
    service: ResourceServiceDep, unit_id: UUID
) -> Position | None:
    unit = await service.get_unit(unit_id)
    if unit.vehicle_resource_id is None:
        return None
    return await service.get_location(unit.vehicle_resource_id)


# ---------------------------------------------------------------- vehicles ---
@router.get("/vehicles", response_model=list[VehicleResponse], summary="List vehicles")
async def list_vehicles(
    service: ResourceServiceDep,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[VehicleResponse]:
    vehicles = await service.list_vehicles(limit=limit, offset=offset)
    states = await service.vehicle_states([v.id for v in vehicles])
    return [vehicle_to_response(v, states.get(v.id)) for v in vehicles]


@router.get(
    "/vehicles/{resource_id}", response_model=VehicleResponse, summary="Get vehicle"
)
async def get_vehicle(
    service: ResourceServiceDep, resource_id: UUID
) -> VehicleResponse:
    vehicle = await service.get_vehicle(resource_id)
    states = await service.vehicle_states([resource_id])
    return vehicle_to_response(vehicle, states.get(resource_id))


@router.patch(
    "/vehicles/{resource_id}/status", response_model=VehicleResponse,
    summary="Change vehicle status",
)
async def update_vehicle_status(
    service: ResourceServiceDep, resource_id: UUID, data: StatusUpdateRequest
) -> VehicleResponse:
    await service.update_resource_status(
        resource_id, data.status_code,
        event=ResourceEventType.VEHICLE_STATUS_CHANGED,
        actor_name=data.actor_name, reason=data.reason,
        incident_id=data.incident_id,
    )
    vehicle = await service.get_vehicle(resource_id)
    states = await service.vehicle_states([resource_id])
    return vehicle_to_response(vehicle, states.get(resource_id))


# --------------------------------------------------------- crews / personnel ---
@router.get("/crews", response_model=list[CrewResponse], summary="List crews")
async def list_crews(
    service: ResourceServiceDep,
    on_duty: bool | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
) -> list[CrewResponse]:
    crews = await service.list_crews(on_duty=on_duty, limit=limit)
    return [crew_to_response(c) for c in crews]


@router.post(
    "/crews/{crew_id}/composition", response_model=CrewResponse,
    summary="Change crew composition",
)
async def change_crew(
    service: ResourceServiceDep, crew_id: UUID, data: CrewCompositionChange
) -> CrewResponse:
    crew = await service.change_crew_composition(
        crew_id,
        add=data.add_personnel_resource_ids,
        remove=data.remove_personnel_resource_ids,
        actor_name=data.actor_name,
    )
    return crew_to_response(crew)


@router.get(
    "/personnel", response_model=list[PersonnelResponse], summary="List personnel"
)
async def list_personnel(
    service: ResourceServiceDep,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[PersonnelResponse]:
    people = await service.list_personnel(limit=limit, offset=offset)
    quals = await service.qualifications([p.id for p in people])
    return [personnel_to_response(p, quals.get(p.id, [])) for p in people]


@router.patch(
    "/personnel/{resource_id}/status", response_model=PersonnelResponse,
    summary="Change personnel status",
)
async def update_personnel_status(
    service: ResourceServiceDep, resource_id: UUID, data: StatusUpdateRequest
) -> PersonnelResponse:
    await service.update_resource_status(
        resource_id, data.status_code,
        event=ResourceEventType.PERSONNEL_STATUS_CHANGED,
        actor_name=data.actor_name, reason=data.reason,
    )
    person = await service.get_personnel(resource_id)
    quals = await service.qualifications([resource_id])
    return personnel_to_response(person, quals.get(resource_id, []))


# --------------------------------------------------------------- resources ---
@router.post(
    "/resources/bulk-status", status_code=status.HTTP_200_OK,
    summary="Bulk status update",
)
async def bulk_status(
    service: ResourceServiceDep, data: BulkStatusUpdateRequest
) -> dict[str, int]:
    updated = await service.bulk_update_status(
        data.resource_ids, data.status_code,
        actor_name=data.actor_name, reason=data.reason,
    )
    return {"updated": updated}


@router.get(
    "/resources/status", response_model=list[StatusOverviewItem],
    summary="Status overview",
)
async def resources_status(
    service: ResourceServiceDep,
) -> list[StatusOverviewItem]:
    return [overview_item(s, c) for s, c in await service.status_overview()]


@router.get(
    "/resources/history", response_model=list[HistoryEntryResponse],
    summary="Resource change history",
)
async def resources_history(
    service: ResourceServiceDep,
    resource_id: UUID | None = Query(default=None),
    unit_id: UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[HistoryEntryResponse]:
    rows = await service.history(
        resource_id=resource_id, unit_id=unit_id, limit=limit, offset=offset
    )
    return [history_to_response(r) for r in rows]
