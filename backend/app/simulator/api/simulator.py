"""REST API for the simulation & training platform (Stage 17 §9).

Routes are mounted under ``/training``. The platform is isolated from the live
system: no endpoint reads or writes the production database.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.simulator.api.deps import SimulatorServiceDep
from app.simulator.scenarios.store import ScenarioNotFoundError
from app.simulator.schemas.mapping import (
    report_to_response,
    scenario_from_create,
    scenario_to_detail,
    scenario_to_summary,
    session_to_response,
)
from app.simulator.schemas.simulator import (
    ActionResponse,
    ControlRequest,
    DispatchRequest,
    ReportResponse,
    ResolveRequest,
    ScenarioCreate,
    ScenarioDetail,
    ScenarioSummary,
    SessionResponse,
    StartRequest,
    StatisticsResponse,
    StopRequest,
)
from app.simulator.services.service import SessionAlreadyEndedError
from app.simulator.services.session import SessionNotFoundError

router = APIRouter(prefix="/training", tags=["training"])


def _scenario_or_404(service: SimulatorServiceDep, scenario_id: str):
    try:
        return service.get_scenario(scenario_id)
    except ScenarioNotFoundError as exc:
        raise NotFoundError(f"Scenario not found: {scenario_id}") from exc


def _session_or_404(service, session_id: str):
    try:
        return service.get_session(session_id)
    except SessionNotFoundError as exc:
        raise NotFoundError(f"Session not found: {session_id}") from exc


# ---------------------------------------------------------------- scenarios ---
@router.get("/scenarios", response_model=list[ScenarioSummary])
async def list_scenarios(service: SimulatorServiceDep) -> list[ScenarioSummary]:
    return [scenario_to_summary(s) for s in service.list_scenarios()]


@router.post(
    "/scenarios",
    response_model=ScenarioDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_scenario(
    payload: ScenarioCreate, service: SimulatorServiceDep
) -> ScenarioDetail:
    try:
        scenario = scenario_from_create(payload)
    except (ValueError, KeyError) as exc:
        raise ValidationError(f"Invalid scenario: {exc}") from exc
    return scenario_to_detail(service.create_scenario(scenario))


@router.get("/scenarios/{scenario_id}", response_model=ScenarioDetail)
async def get_scenario(
    scenario_id: str, service: SimulatorServiceDep
) -> ScenarioDetail:
    return scenario_to_detail(_scenario_or_404(service, scenario_id))


# ------------------------------------------------------------------ session ---
@router.post("/start", response_model=SessionResponse)
async def start_training(
    payload: StartRequest, service: SimulatorServiceDep
) -> SessionResponse:
    try:
        session = service.start(
            payload.scenario_id,
            trainee=payload.trainee,
            speed=payload.speed,
            mode=payload.mode,
        )
    except ScenarioNotFoundError as exc:
        raise NotFoundError(f"Scenario not found: {payload.scenario_id}") from exc
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    return session_to_response(session)


@router.post("/stop", response_model=ReportResponse)
async def stop_training(
    payload: StopRequest, service: SimulatorServiceDep
) -> ReportResponse:
    try:
        report = service.stop(payload.session_id)
    except SessionNotFoundError as exc:
        raise NotFoundError(f"Session not found: {payload.session_id}") from exc
    return report_to_response(report)


@router.get("/results", response_model=list[ReportResponse])
async def get_results(
    service: SimulatorServiceDep,
    session_id: str | None = Query(default=None),
) -> list[ReportResponse]:
    try:
        reports = service.results(session_id)
    except SessionNotFoundError as exc:
        raise NotFoundError(f"Session not found: {session_id}") from exc
    return [report_to_response(r) for r in reports]


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(service: SimulatorServiceDep) -> StatisticsResponse:
    return StatisticsResponse(**service.statistics())


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str, service: SimulatorServiceDep
) -> SessionResponse:
    return session_to_response(_session_or_404(service, session_id))


@router.post("/sessions/{session_id}/dispatch", response_model=ActionResponse)
async def dispatch(
    session_id: str, payload: DispatchRequest, service: SimulatorServiceDep
) -> ActionResponse:
    try:
        outcome = service.dispatch(session_id, payload.incident_id, payload.unit_ids)
    except SessionNotFoundError as exc:
        raise NotFoundError(f"Session not found: {session_id}") from exc
    except SessionAlreadyEndedError as exc:
        raise ConflictError(str(exc)) from exc
    return ActionResponse(
        accepted=outcome.accepted,
        message=outcome.message,
        incident_id=outcome.incident_id,
    )


@router.post("/sessions/{session_id}/resolve", response_model=ActionResponse)
async def resolve(
    session_id: str, payload: ResolveRequest, service: SimulatorServiceDep
) -> ActionResponse:
    try:
        outcome = service.resolve(session_id, payload.incident_id)
    except SessionNotFoundError as exc:
        raise NotFoundError(f"Session not found: {session_id}") from exc
    except SessionAlreadyEndedError as exc:
        raise ConflictError(str(exc)) from exc
    return ActionResponse(
        accepted=outcome.accepted,
        message=outcome.message,
        incident_id=outcome.incident_id,
    )


@router.post("/sessions/{session_id}/control", response_model=SessionResponse)
async def control(
    session_id: str, payload: ControlRequest, service: SimulatorServiceDep
) -> SessionResponse:
    op = payload.op.lower()
    try:
        if op == "pause":
            session = service.pause(session_id)
        elif op == "resume":
            session = service.resume(session_id)
        elif op == "step":
            session = service.step(session_id)
        elif op == "advance":
            if payload.seconds is None:
                raise ValidationError("'advance' requires 'seconds'")
            session = service.advance(session_id, payload.seconds)
        elif op == "set_speed":
            if payload.speed is None:
                raise ValidationError("'set_speed' requires 'speed'")
            session = service.set_speed(session_id, payload.speed)
        else:
            raise ValidationError(f"unknown control op: {payload.op}")
    except SessionNotFoundError as exc:
        raise NotFoundError(f"Session not found: {session_id}") from exc
    except SessionAlreadyEndedError as exc:
        raise ConflictError(str(exc)) from exc
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    return session_to_response(session)
