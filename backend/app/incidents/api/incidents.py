"""Incident management REST endpoints.

    POST   /incidents                  — create an incident
    GET    /incidents                  — list incidents (summaries)
    GET    /incidents/active           — active incidents
    GET    /incidents/archive          — closed / archived incidents
    GET    /incidents/{id}             — one incident (full card)
    PUT    /incidents/{id}             — update card metadata (audited)
    PATCH  /incidents/{id}/status      — change lifecycle status (state machine)
    GET    /incidents/{id}/timeline    — the incident's chronology
    POST   /incidents/{id}/comments    — add a dispatcher comment
    POST   /incidents/{id}/units       — assign / dispatch units (integration)
    POST   /incidents/{id}/recommend   — get a recommendation via Dispatch Engine
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.core.exceptions import ValidationError
from app.incidents.deps import IncidentServiceDep
from app.incidents.schemas.incident import (
    AssignUnitsRequest,
    CommentCreate,
    CommentResponse,
    IncidentCreate,
    IncidentResponse,
    IncidentSummaryResponse,
    IncidentTimelineResponse,
    IncidentUpdate,
    StatusChangeRequest,
    StatusResponse,
    TimelineEntryResponse,
)
from app.incidents.utils.mapping import incident_to_response, incident_to_summary
from app.incidents.validators.state_machine import allowed_targets

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post(
    "", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED,
    summary="Create an incident",
)
async def create_incident(
    service: IncidentServiceDep, data: IncidentCreate
) -> IncidentResponse:
    return incident_to_response(await service.create(data))


@router.get("", response_model=list[IncidentSummaryResponse], summary="List incidents")
async def list_incidents(
    service: IncidentServiceDep,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[IncidentSummaryResponse]:
    rows = await service.list_incidents(limit=limit, offset=offset)
    return [incident_to_summary(r) for r in rows]


@router.get(
    "/active", response_model=list[IncidentSummaryResponse],
    summary="Active incidents",
)
async def active_incidents(
    service: IncidentServiceDep,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[IncidentSummaryResponse]:
    rows = await service.list_incidents(active=True, limit=limit)
    return [incident_to_summary(r) for r in rows]


@router.get(
    "/archive", response_model=list[IncidentSummaryResponse],
    summary="Closed / archived incidents",
)
async def archived_incidents(
    service: IncidentServiceDep,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[IncidentSummaryResponse]:
    rows = await service.list_incidents(active=False, limit=limit)
    return [incident_to_summary(r) for r in rows]


@router.get(
    "/{incident_id}/timeline",
    response_model=IncidentTimelineResponse,
    summary="Incident timeline",
)
async def incident_timeline(
    service: IncidentServiceDep, incident_id: UUID
) -> IncidentTimelineResponse:
    incident = await service.get(incident_id)
    entries = sorted(
        (TimelineEntryResponse.model_validate(e) for e in incident.timeline),
        key=lambda e: e.occurred_at,
    )
    return IncidentTimelineResponse(
        incident_id=incident.id, count=len(entries), entries=entries
    )


@router.get("/{incident_id}", response_model=IncidentResponse, summary="Get incident")
async def get_incident(
    service: IncidentServiceDep, incident_id: UUID
) -> IncidentResponse:
    return incident_to_response(await service.get(incident_id))


@router.put(
    "/{incident_id}", response_model=IncidentResponse, summary="Update incident"
)
async def update_incident(
    service: IncidentServiceDep, incident_id: UUID, data: IncidentUpdate
) -> IncidentResponse:
    return incident_to_response(await service.update(incident_id, data))


@router.patch(
    "/{incident_id}/status", response_model=StatusResponse,
    summary="Change incident status",
)
async def change_status(
    service: IncidentServiceDep, incident_id: UUID, data: StatusChangeRequest
) -> StatusResponse:
    incident = await service.change_status(incident_id, data)
    return StatusResponse(
        id=incident.id,
        status=incident.status,
        allowed_transitions=sorted(
            allowed_targets(incident.status), key=lambda s: s.value
        ),
        changed_at=datetime.now(tz=UTC),
    )


@router.post(
    "/{incident_id}/comments", response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED, summary="Add a comment",
)
async def add_comment(
    service: IncidentServiceDep, incident_id: UUID, data: CommentCreate
) -> CommentResponse:
    incident = await service.add_comment(incident_id, data)
    latest = max(incident.comments, key=lambda c: c.created_at)
    return CommentResponse.model_validate(latest)


@router.post(
    "/{incident_id}/units", response_model=IncidentResponse, summary="Assign units",
)
async def assign_units(
    service: IncidentServiceDep, incident_id: UUID, data: AssignUnitsRequest
) -> IncidentResponse:
    return incident_to_response(await service.assign_units(incident_id, data))


@router.post(
    "/{incident_id}/recommend", response_model=IncidentResponse,
    summary="Request a dispatch recommendation (Dispatch Engine)",
)
async def request_recommendation(
    service: IncidentServiceDep, incident_id: UUID, actor_name: str | None = None
) -> IncidentResponse:
    if actor_name == "":
        raise ValidationError("actor_name must not be empty")
    return incident_to_response(
        await service.request_recommendation(incident_id, actor_name=actor_name)
    )
