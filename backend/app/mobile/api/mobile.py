"""REST API for the mobile platform (Stage 19).

Two thin BFF surfaces mounted under ``/mobile``: ``/mobile/commander`` for the
command staff and ``/mobile/responder`` for field units, plus device
registration and offline sync. All decisions are made server-side here; the apps
only render responses and send actions.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.mobile.api.deps import MobilePlatformDep
from app.mobile.push.base import Device
from app.mobile.schemas.mobile import (
    DashboardResponse,
    DeviceRegisterRequest,
    DeviceRegisterResponse,
    DispatchResponse,
    IncidentView,
    MapResponse,
    MessageRequest,
    MessageView,
    NoteRequest,
    NoteView,
    ResourceView,
    RouteResponse,
    StatusUpdateRequest,
    StatusUpdateResponse,
    SyncBatchRequest,
    SyncBatchResponse,
    SyncResultView,
)
from app.mobile.services.offline import SyncOperation
from app.mobile.services.responder import ResponderError
from app.mobile.services.status import InvalidStatusTransition, ResponderStatus

router = APIRouter(prefix="/mobile", tags=["mobile"])


# ============================================================== commander ====
commander = APIRouter(prefix="/commander")


@commander.get("/dashboard", response_model=DashboardResponse)
async def commander_dashboard(platform: MobilePlatformDep) -> DashboardResponse:
    d = platform.commander.dashboard()
    return DashboardResponse(
        summary=d.summary.__dict__,
        active_incidents=[IncidentView(**i.__dict__) for i in d.active_incidents],
        resource_load=[ResourceView(**r.__dict__) for r in d.resource_load],
        critical=[c.__dict__ for c in d.critical],
    )


@commander.get("/incidents", response_model=list[IncidentView])
async def commander_incidents(
    platform: MobilePlatformDep,
    active_only: bool = Query(default=True),
) -> list[IncidentView]:
    return [
        IncidentView(**i.__dict__)
        for i in platform.commander.incidents(active_only=active_only)
    ]


@commander.get("/resources", response_model=list[ResourceView])
async def commander_resources(platform: MobilePlatformDep) -> list[ResourceView]:
    return [ResourceView(**r.__dict__) for r in platform.commander.resources()]


@commander.get("/map", response_model=MapResponse)
async def commander_map(platform: MobilePlatformDep) -> MapResponse:
    data = platform.commander.map_data()
    return MapResponse(
        incidents=[IncidentView(**i.__dict__) for i in data["incidents"]],
        units=[ResourceView(**r.__dict__) for r in data["units"]],
    )


@commander.post("/notes", response_model=NoteView, status_code=status.HTTP_201_CREATED)
async def commander_add_note(
    payload: NoteRequest, platform: MobilePlatformDep
) -> NoteView:
    if not payload.text.strip():
        raise ValidationError("note text is empty")
    note = platform.commander.add_note(
        author=payload.author, text=payload.text,
        incident_id=payload.incident_id, kind=payload.kind,
    )
    return NoteView(**note.__dict__)


# ============================================================== responder ====
responder = APIRouter(prefix="/responder")


@responder.get("/dispatch", response_model=DispatchResponse)
async def responder_dispatch(
    platform: MobilePlatformDep, unit_id: str = Query(...)
) -> DispatchResponse:
    try:
        card = platform.responder.dispatch(unit_id)
    except ResponderError as exc:
        raise NotFoundError(str(exc)) from exc
    return DispatchResponse(
        **card.__dict__,
        current_status=platform.responder.current_status(unit_id).value,
    )


@responder.get("/route", response_model=RouteResponse)
async def responder_route(
    platform: MobilePlatformDep, unit_id: str = Query(...)
) -> RouteResponse:
    try:
        route = platform.responder.route(unit_id)
    except ResponderError as exc:
        raise NotFoundError(str(exc)) from exc
    return RouteResponse(
        points=[p.__dict__ for p in route.points],
        distance_km=route.distance_km,
        eta_seconds=route.eta_seconds,
    )


@responder.patch("/status", response_model=StatusUpdateResponse)
async def responder_status(
    payload: StatusUpdateRequest, platform: MobilePlatformDep
) -> StatusUpdateResponse:
    try:
        target = ResponderStatus(payload.status)
    except ValueError as exc:
        raise ValidationError(f"unknown status: {payload.status}") from exc
    try:
        new = platform.responder.update_status(payload.unit_id, target)
    except InvalidStatusTransition as exc:
        raise ConflictError(str(exc)) from exc
    return StatusUpdateResponse(unit_id=payload.unit_id, status=new.value)


@responder.post(
    "/message", response_model=MessageView, status_code=status.HTTP_201_CREATED
)
async def responder_message(
    payload: MessageRequest, platform: MobilePlatformDep
) -> MessageView:
    try:
        msg = platform.responder.send_message(
            payload.unit_id,
            from_user=payload.from_user or payload.unit_id,
            text=payload.text,
            incident_id=payload.incident_id,
        )
    except ResponderError as exc:
        raise ValidationError(str(exc)) from exc
    return MessageView(**msg.__dict__)


# ================================================================ push/sync ===
@router.post(
    "/devices", response_model=DeviceRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_device(
    payload: DeviceRegisterRequest, platform: MobilePlatformDep
) -> DeviceRegisterResponse:
    device = platform.push.register(
        Device(token=payload.token, user_id=payload.user_id,
               platform=payload.platform, app=payload.app)
    )
    return DeviceRegisterResponse(registered=True, token=device.token)


@router.delete("/devices/{token}")
async def unregister_device(
    token: str, platform: MobilePlatformDep
) -> dict[str, bool]:
    return {"unregistered": platform.push.unregister(token)}


@router.post("/sync", response_model=SyncBatchResponse)
async def sync_batch(
    payload: SyncBatchRequest, platform: MobilePlatformDep
) -> SyncBatchResponse:
    ops = [
        SyncOperation(op_id=o.op_id, type=o.type, payload=o.payload)
        for o in payload.operations
    ]
    results = platform.process_sync(ops)
    return SyncBatchResponse(
        results=[SyncResultView(**r.__dict__) for r in results]
    )


router.include_router(commander)
router.include_router(responder)
