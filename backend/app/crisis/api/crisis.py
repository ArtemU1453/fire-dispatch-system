"""REST API for the Crisis Management Platform (Stage 20 §10).

Mounted under ``/crisis``. An overlay: it manages large-scale operations without
touching the Dispatch Engine, incidents or GIS. All actions are journalled and
RBAC-gated (open when no user is identified).
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.crisis.api.deps import (
    ActorDep,
    BoardServiceDep,
    JournalServiceDep,
    OperationServiceDep,
    PlanServiceDep,
    ReportServiceDep,
    ResourceServiceDep,
    SectorServiceDep,
    UserIdDep,
)
from app.crisis.models.enums import JournalKind
from app.crisis.schemas.crisis import (
    CommandAssignCreate,
    CommanderResponse,
    DecisionCreate,
    DecisionResponse,
    HeadquartersResponse,
    JournalEntryResponse,
    OperationCreate,
    OperationResponse,
    OperationUpdate,
    OrderCreate,
    OrderResponse,
    PlanStageResponse,
    RelocateRequest,
    ReportCreate,
    ResourceGroupCreate,
    ResourceGroupResponse,
    ResourceMemberCreate,
    ResourceMemberResponse,
    ResourceMoveResponse,
    ResponseLevelResponse,
    SectorCreate,
    SectorResponse,
    SectorUpdate,
    SituationBoardResponse,
    SituationReportResponse,
    StageCreate,
    StatusUpdate,
    TaskCreate,
    TaskResponse,
    ZoneCreate,
    ZoneResponse,
)

router = APIRouter(prefix="/crisis", tags=["crisis"])

_CREATED = status.HTTP_201_CREATED


# ------------------------------------------------------------- operations ----
@router.get("/levels", response_model=list[ResponseLevelResponse])
async def list_levels(service: OperationServiceDep) -> list[ResponseLevelResponse]:
    levels = await service.list_levels()
    return [ResponseLevelResponse.model_validate(x) for x in levels]


@router.get("/operations", response_model=list[OperationResponse])
async def list_operations(
    service: OperationServiceDep,
    user_id: UserIdDep,
    op_status: str | None = Query(default=None, alias="status"),
) -> list[OperationResponse]:
    ops = await service.list(status=op_status, user_id=user_id)
    return [OperationResponse.model_validate(o) for o in ops]


@router.post("/operations", response_model=OperationResponse, status_code=_CREATED)
async def create_operation(
    payload: OperationCreate,
    service: OperationServiceDep,
    actor: ActorDep,
    user_id: UserIdDep,
) -> OperationResponse:
    op = await service.create(
        name=payload.name,
        code=payload.code,
        response_level_code=payload.response_level_code,
        incident_ref=payload.incident_ref,
        description=payload.description,
        started_at=payload.started_at,
        actor=actor,
        user_id=user_id,
    )
    return OperationResponse.model_validate(op)


@router.get("/{operation_id}", response_model=OperationResponse)
async def get_operation(
    operation_id: UUID, service: OperationServiceDep, user_id: UserIdDep
) -> OperationResponse:
    return OperationResponse.model_validate(
        await service.get(operation_id, user_id=user_id)
    )


@router.patch("/{operation_id}", response_model=OperationResponse)
async def update_operation(
    operation_id: UUID,
    payload: OperationUpdate,
    service: OperationServiceDep,
    actor: ActorDep,
    user_id: UserIdDep,
) -> OperationResponse:
    op = await service.update(
        operation_id,
        values=payload.model_dump(exclude_unset=True),
        actor=actor,
        user_id=user_id,
    )
    return OperationResponse.model_validate(op)


# ----------------------------------------------------------- headquarters ----
@router.get("/{operation_id}/headquarters", response_model=HeadquartersResponse)
async def get_headquarters(
    operation_id: UUID, service: OperationServiceDep, user_id: UserIdDep
) -> HeadquartersResponse:
    return HeadquartersResponse.model_validate(
        await service.headquarters(operation_id, user_id=user_id)
    )


@router.post(
    "/{operation_id}/command", response_model=CommanderResponse, status_code=_CREATED
)
async def assign_command(
    operation_id: UUID,
    payload: CommandAssignCreate,
    service: OperationServiceDep,
    actor: ActorDep,
    user_id: UserIdDep,
) -> CommanderResponse:
    a = await service.assign_command(
        operation_id,
        role=payload.role,
        user_ref=payload.user_ref,
        display_name=payload.display_name,
        responsibilities=payload.responsibilities,
        actor=actor,
        user_id=user_id,
    )
    return CommanderResponse.model_validate(a)


@router.get("/{operation_id}/command", response_model=list[CommanderResponse])
async def list_command(
    operation_id: UUID, service: OperationServiceDep, user_id: UserIdDep
) -> list[CommanderResponse]:
    members = await service.command_members(operation_id, user_id=user_id)
    return [CommanderResponse.model_validate(m) for m in members]


@router.post(
    "/{operation_id}/decision", response_model=DecisionResponse, status_code=_CREATED
)
async def record_decision(
    operation_id: UUID,
    payload: DecisionCreate,
    service: OperationServiceDep,
    actor: ActorDep,
    user_id: UserIdDep,
) -> DecisionResponse:
    entry = await service.record_decision(
        operation_id,
        decision=payload.decision,
        rationale=payload.rationale,
        actor=actor,
        user_id=user_id,
    )
    return DecisionResponse.model_validate(entry)


# --------------------------------------------------------------- sectors ----
@router.post(
    "/{operation_id}/sector", response_model=SectorResponse, status_code=_CREATED
)
async def create_sector(
    operation_id: UUID,
    payload: SectorCreate,
    service: SectorServiceDep,
    actor: ActorDep,
    user_id: UserIdDep,
) -> SectorResponse:
    sector = await service.create_sector(
        operation_id,
        name=payload.name,
        leader_ref=payload.leader_ref,
        center_lat=payload.center_lat,
        center_lon=payload.center_lon,
        actor=actor,
        user_id=user_id,
    )
    return SectorResponse.model_validate(sector)


@router.get("/{operation_id}/sectors", response_model=list[SectorResponse])
async def list_sectors(
    operation_id: UUID, service: SectorServiceDep, user_id: UserIdDep
) -> list[SectorResponse]:
    return [
        SectorResponse.model_validate(s)
        for s in await service.list_sectors(operation_id, user_id=user_id)
    ]


@router.patch("/sectors/{sector_id}", response_model=SectorResponse)
async def update_sector(
    sector_id: UUID,
    payload: SectorUpdate,
    service: SectorServiceDep,
    actor: ActorDep,
    user_id: UserIdDep,
) -> SectorResponse:
    sector = await service.update_sector(
        sector_id,
        values=payload.model_dump(exclude_unset=True),
        actor=actor,
        user_id=user_id,
    )
    return SectorResponse.model_validate(sector)


@router.post(
    "/{operation_id}/zone", response_model=ZoneResponse, status_code=_CREATED
)
async def create_zone(
    operation_id: UUID,
    payload: ZoneCreate,
    service: SectorServiceDep,
    user_id: UserIdDep,
) -> ZoneResponse:
    zone = await service.create_zone(
        operation_id,
        label=payload.label,
        kind=payload.kind,
        sector_id=payload.sector_id,
        center_lat=payload.center_lat,
        center_lon=payload.center_lon,
        radius_m=payload.radius_m,
        user_id=user_id,
    )
    return ZoneResponse.model_validate(zone)


# ------------------------------------------------------------- resources ----
@router.post(
    "/{operation_id}/resource-group",
    response_model=ResourceGroupResponse,
    status_code=_CREATED,
)
async def create_resource_group(
    operation_id: UUID,
    payload: ResourceGroupCreate,
    service: ResourceServiceDep,
    actor: ActorDep,
    user_id: UserIdDep,
) -> ResourceGroupResponse:
    group = await service.create_group(
        operation_id,
        name=payload.name,
        purpose=payload.purpose,
        sector_id=payload.sector_id,
        actor=actor,
        user_id=user_id,
    )
    return ResourceGroupResponse.model_validate(group)


@router.get(
    "/{operation_id}/resource-groups", response_model=list[ResourceGroupResponse]
)
async def list_resource_groups(
    operation_id: UUID, service: ResourceServiceDep, user_id: UserIdDep
) -> list[ResourceGroupResponse]:
    return [
        ResourceGroupResponse.model_validate(g)
        for g in await service.list_groups(operation_id, user_id=user_id)
    ]


@router.post(
    "/resource-groups/{group_id}/members",
    response_model=ResourceMemberResponse,
    status_code=_CREATED,
)
async def add_member(
    group_id: UUID,
    payload: ResourceMemberCreate,
    service: ResourceServiceDep,
    actor: ActorDep,
    user_id: UserIdDep,
) -> ResourceMemberResponse:
    member = await service.add_member(
        group_id, kind=payload.kind, ref=payload.ref, label=payload.label,
        actor=actor, user_id=user_id,
    )
    return ResourceMemberResponse.model_validate(member)


@router.post(
    "/resource-groups/{group_id}/relocate",
    response_model=ResourceMoveResponse,
    status_code=_CREATED,
)
async def relocate_group(
    group_id: UUID,
    payload: RelocateRequest,
    service: ResourceServiceDep,
    actor: ActorDep,
    user_id: UserIdDep,
) -> ResourceMoveResponse:
    move = await service.relocate(
        group_id, to_sector_id=payload.to_sector_id, note=payload.note,
        actor=actor, user_id=user_id,
    )
    return ResourceMoveResponse.model_validate(move)


@router.get(
    "/resource-groups/{group_id}/history", response_model=list[ResourceMoveResponse]
)
async def group_history(
    group_id: UUID, service: ResourceServiceDep
) -> list[ResourceMoveResponse]:
    return [
        ResourceMoveResponse.model_validate(m)
        for m in await service.move_history(group_id)
    ]


# ------------------------------------------------------------ plan/tasks ----
@router.post(
    "/{operation_id}/plan/stages",
    response_model=PlanStageResponse,
    status_code=_CREATED,
)
async def add_stage(
    operation_id: UUID,
    payload: StageCreate,
    service: PlanServiceDep,
    user_id: UserIdDep,
) -> PlanStageResponse:
    stage = await service.add_stage(
        operation_id, name=payload.name, position=payload.position, user_id=user_id
    )
    return PlanStageResponse.model_validate(stage)


@router.get("/{operation_id}/plan/stages", response_model=list[PlanStageResponse])
async def list_stages(
    operation_id: UUID, service: PlanServiceDep, user_id: UserIdDep
) -> list[PlanStageResponse]:
    return [
        PlanStageResponse.model_validate(s)
        for s in await service.list_stages(operation_id, user_id=user_id)
    ]


@router.post("/{operation_id}/tasks", response_model=TaskResponse, status_code=_CREATED)
async def add_task(
    operation_id: UUID,
    payload: TaskCreate,
    service: PlanServiceDep,
    actor: ActorDep,
    user_id: UserIdDep,
) -> TaskResponse:
    task = await service.add_task(
        operation_id,
        title=payload.title,
        description=payload.description,
        stage_id=payload.stage_id,
        sector_id=payload.sector_id,
        assignee_ref=payload.assignee_ref,
        due_at=payload.due_at,
        actor=actor,
        user_id=user_id,
    )
    return TaskResponse.model_validate(task)


@router.get("/{operation_id}/tasks", response_model=list[TaskResponse])
async def list_tasks(
    operation_id: UUID,
    service: PlanServiceDep,
    user_id: UserIdDep,
    sector_id: UUID | None = Query(default=None),
) -> list[TaskResponse]:
    tasks = await service.list_tasks(
        operation_id, sector_id=sector_id, user_id=user_id
    )
    return [TaskResponse.model_validate(t) for t in tasks]


@router.patch("/tasks/{task_id}/status", response_model=TaskResponse)
async def set_task_status(
    task_id: UUID,
    payload: StatusUpdate,
    service: PlanServiceDep,
    actor: ActorDep,
    user_id: UserIdDep,
) -> TaskResponse:
    task = await service.set_task_status(
        task_id, payload.status, actor=actor, user_id=user_id
    )
    return TaskResponse.model_validate(task)


# ------------------------------------------------- timeline / reports / board
@router.get("/{operation_id}/timeline", response_model=list[JournalEntryResponse])
async def get_timeline(
    operation_id: UUID,
    service: JournalServiceDep,
    kind: str | None = Query(default=None),
) -> list[JournalEntryResponse]:
    jk = JournalKind(kind) if kind else None
    entries = await service.timeline(operation_id, kind=jk)
    return [JournalEntryResponse.model_validate(e) for e in entries]


@router.post(
    "/{operation_id}/reports",
    response_model=SituationReportResponse,
    status_code=_CREATED,
)
async def add_report(
    operation_id: UUID,
    payload: ReportCreate,
    service: ReportServiceDep,
    user_id: UserIdDep,
) -> SituationReportResponse:
    report = await service.add_report(
        operation_id, summary=payload.summary, author_ref=payload.author_ref,
        data=payload.data, user_id=user_id,
    )
    return SituationReportResponse.model_validate(report)


@router.get("/{operation_id}/reports", response_model=list[SituationReportResponse])
async def list_reports(
    operation_id: UUID, service: ReportServiceDep, user_id: UserIdDep
) -> list[SituationReportResponse]:
    return [
        SituationReportResponse.model_validate(r)
        for r in await service.list_reports(operation_id, user_id=user_id)
    ]


@router.post(
    "/{operation_id}/orders", response_model=OrderResponse, status_code=_CREATED
)
async def add_order(
    operation_id: UUID,
    payload: OrderCreate,
    service: ReportServiceDep,
    user_id: UserIdDep,
) -> OrderResponse:
    order = await service.add_order(
        operation_id, number=payload.number, text=payload.text,
        issued_by_ref=payload.issued_by_ref, user_id=user_id,
    )
    return OrderResponse.model_validate(order)


@router.get("/{operation_id}/board", response_model=SituationBoardResponse)
async def situation_board(
    operation_id: UUID, service: BoardServiceDep, user_id: UserIdDep
) -> SituationBoardResponse:
    board = await service.board(operation_id, user_id=user_id)
    return SituationBoardResponse(
        operation_id=board["operation_id"],
        sectors=[SectorResponse.model_validate(s) for s in board["sectors"]],
        zones=[ZoneResponse.model_validate(z) for z in board["zones"]],
        resource_groups=[
            ResourceGroupResponse.model_validate(g) for g in board["resource_groups"]
        ],
        critical_events=[
            JournalEntryResponse.model_validate(e) for e in board["critical_events"]
        ],
        latest_report=(
            SituationReportResponse.model_validate(board["latest_report"])
            if board["latest_report"] is not None
            else None
        ),
    )
