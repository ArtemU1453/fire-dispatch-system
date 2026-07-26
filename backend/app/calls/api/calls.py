"""Call-management REST endpoints.

    POST  /calls                     · GET /calls · GET /calls/{id}
    PATCH /calls/{id}/status         · POST /calls/{id}/incident
    GET   /calls/queue               · GET /calls/history
    (+ dispatcher assignment, telephony actions and provider health)

The literal ``/calls/queue``, ``/calls/history`` and ``/calls/provider/health``
routes are declared **before** the dynamic ``/calls/{call_id}`` so they are not
shadowed.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.calls.deps import CallServiceDep
from app.calls.schemas.call import (
    AssignDispatcherRequest,
    CallCreate,
    CallHistoryResponse,
    CallQueueResponse,
    CallResponse,
    CallSummaryResponse,
    CallUpdate,
    LinkIncidentRequest,
    ProviderHealthResponse,
    TransferCallRequest,
)
from app.calls.utils.actor import Actor
from app.calls.utils.mapping import (
    call_to_response,
    call_to_summary,
    history_to_response,
    queue_entry_to_response,
)

router = APIRouter(prefix="/calls", tags=["calls"])


def _actor(name: str | None) -> Actor:
    return Actor(name=name)


# ---------------------------------------------------------------- literal ---
@router.get(
    "/queue", response_model=list[CallQueueResponse], summary="Call queue"
)
async def get_queue(
    service: CallServiceDep,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[CallQueueResponse]:
    entries = await service.get_queue(limit=limit, offset=offset)
    return [queue_entry_to_response(e) for e in entries]


@router.get(
    "/history", response_model=list[CallHistoryResponse],
    summary="Call history (global or by call)",
)
async def get_history(
    service: CallServiceDep,
    call_id: UUID | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[CallHistoryResponse]:
    rows = await service.get_history(call_id=call_id, limit=limit, offset=offset)
    return [history_to_response(r) for r in rows]


@router.get(
    "/provider/health", response_model=ProviderHealthResponse,
    summary="Telephony provider health",
)
async def provider_health(service: CallServiceDep) -> ProviderHealthResponse:
    health = await service.provider_health()
    return ProviderHealthResponse(
        healthy=health.healthy, provider=health.provider, detail=health.detail
    )


# --------------------------------------------------------------- calls ---
@router.post(
    "", response_model=CallResponse, status_code=status.HTTP_201_CREATED,
    summary="Register a call",
)
async def create_call(
    service: CallServiceDep, data: CallCreate
) -> CallResponse:
    call = await service.create_call(
        direction=data.direction,
        call_type=data.call_type,
        source=data.source,
        priority=data.priority,
        caller_number=data.caller_number,
        caller_name=data.caller_name,
        callee_number=data.callee_number,
        address_hint=data.address_hint,
        notes=data.notes,
        external_id=data.external_id,
        register_with_provider=data.register_with_provider,
        actor=_actor(data.actor_name),
    )
    return call_to_response(call)


@router.get(
    "", response_model=list[CallSummaryResponse], summary="List calls"
)
async def list_calls(
    service: CallServiceDep,
    active: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[CallSummaryResponse]:
    calls = await service.list_calls(active=active, limit=limit, offset=offset)
    return [call_to_summary(c) for c in calls]


@router.get("/{call_id}", response_model=CallResponse, summary="Get a call")
async def get_call(service: CallServiceDep, call_id: UUID) -> CallResponse:
    return call_to_response(await service.get_call(call_id))


@router.patch(
    "/{call_id}/status", response_model=CallResponse,
    summary="Change call status",
)
async def change_status(
    service: CallServiceDep, call_id: UUID, data: CallUpdate
) -> CallResponse:
    call = await service.change_status(
        call_id, data.status, note=data.note, actor=_actor(data.actor_name)
    )
    return call_to_response(call)


@router.post(
    "/{call_id}/incident", response_model=CallResponse,
    summary="Create or link an incident for the call",
)
async def attach_incident(
    service: CallServiceDep, call_id: UUID, data: LinkIncidentRequest
) -> CallResponse:
    call = await service.attach_incident(
        call_id,
        incident_id=data.incident_id,
        create=data.create,
        incident_type_id=data.incident_type_id,
        category=data.category,
        priority=data.priority,
        title=data.title,
        description=data.description,
        address=data.address,
        latitude=data.latitude,
        longitude=data.longitude,
        actor=_actor(data.actor_name),
    )
    return call_to_response(call)


@router.post(
    "/{call_id}/assign", response_model=CallResponse,
    summary="Assign a dispatcher / workstation",
)
async def assign_dispatcher(
    service: CallServiceDep, call_id: UUID, data: AssignDispatcherRequest
) -> CallResponse:
    call = await service.assign_dispatcher(
        call_id,
        dispatcher_user_id=data.dispatcher_user_id,
        dispatcher_name=data.dispatcher_name,
        workstation=data.workstation,
        actor=_actor(data.actor_name),
    )
    return call_to_response(call)


# ------------------------------------------------------- telephony actions ---
@router.post(
    "/{call_id}/answer", response_model=CallResponse, summary="Answer the call"
)
async def answer_call(service: CallServiceDep, call_id: UUID) -> CallResponse:
    return call_to_response(await service.answer_call(call_id))


@router.post(
    "/{call_id}/hold", response_model=CallResponse, summary="Hold the call"
)
async def hold_call(service: CallServiceDep, call_id: UUID) -> CallResponse:
    return call_to_response(await service.hold_call(call_id))


@router.post(
    "/{call_id}/transfer", response_model=CallResponse,
    summary="Transfer the call",
)
async def transfer_call(
    service: CallServiceDep, call_id: UUID, data: TransferCallRequest
) -> CallResponse:
    call = await service.transfer_call(
        call_id, destination=data.destination, actor=_actor(data.actor_name)
    )
    return call_to_response(call)


@router.post(
    "/{call_id}/end", response_model=CallResponse,
    summary="End the call (hang up and complete)",
)
async def end_call(service: CallServiceDep, call_id: UUID) -> CallResponse:
    return call_to_response(await service.end_call(call_id))
