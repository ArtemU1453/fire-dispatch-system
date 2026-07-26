"""REST API for the Digital Twin strategic-analysis platform (Stage 18 §8).

Routes are mounted under ``/digital-twin``. The platform works only with copies
of the data; no endpoint reads or writes the production database.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.core.exceptions import NotFoundError, ValidationError
from app.digital_twin.api.deps import DigitalTwinServiceDep
from app.digital_twin.optimization.optimizer import PlacementCandidate
from app.digital_twin.scenarios.store import ScenarioNotFoundError
from app.digital_twin.schemas.digital_twin import (
    CoverageResponse,
    ForecastRequest,
    ForecastResponse,
    PlacementEvaluationView,
    PlacementRequest,
    ReportResponse,
    ScenarioCreate,
    ScenarioDetail,
    ScenarioSummary,
    SimulateRequest,
    SimulationResultView,
)
from app.digital_twin.schemas.mapping import (
    coverage_to_response,
    forecast_config_from_request,
    forecast_to_response,
    placement_to_view,
    report_to_response,
    scenario_from_create,
    scenario_to_detail,
    scenario_to_summary,
    simulation_result_to_view,
)
from app.digital_twin.simulation.apply import ScenarioApplicationError

router = APIRouter(prefix="/digital-twin", tags=["digital-twin"])


# ---------------------------------------------------------------- scenarios ---
@router.get("/scenarios", response_model=list[ScenarioSummary])
async def list_scenarios(service: DigitalTwinServiceDep) -> list[ScenarioSummary]:
    return [scenario_to_summary(s) for s in service.list_scenarios()]


@router.post(
    "/scenarios",
    response_model=ScenarioDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_scenario(
    payload: ScenarioCreate, service: DigitalTwinServiceDep
) -> ScenarioDetail:
    try:
        scenario = scenario_from_create(payload)
    except (ValueError, KeyError) as exc:
        raise ValidationError(f"Invalid scenario: {exc}") from exc
    return scenario_to_detail(service.create_scenario(scenario))


@router.get("/scenarios/{scenario_id}", response_model=ScenarioDetail)
async def get_scenario(
    scenario_id: str, service: DigitalTwinServiceDep
) -> ScenarioDetail:
    try:
        return scenario_to_detail(service.get_scenario(scenario_id))
    except ScenarioNotFoundError as exc:
        raise NotFoundError(f"Scenario not found: {scenario_id}") from exc


# ----------------------------------------------------------------- simulate ---
@router.post("/simulate", response_model=SimulationResultView)
async def simulate(
    payload: SimulateRequest, service: DigitalTwinServiceDep
) -> SimulationResultView:
    try:
        result = service.simulate(payload.scenario_id)
    except ScenarioNotFoundError as exc:
        raise NotFoundError(f"Scenario not found: {payload.scenario_id}") from exc
    except ScenarioApplicationError as exc:
        raise ValidationError(str(exc)) from exc
    return simulation_result_to_view(result)


@router.get("/results", response_model=list[SimulationResultView])
async def get_results(
    service: DigitalTwinServiceDep,
    result_id: str | None = Query(default=None),
) -> list[SimulationResultView]:
    return [simulation_result_to_view(r) for r in service.results(result_id)]


# ----------------------------------------------------------------- coverage ---
@router.get("/coverage", response_model=CoverageResponse)
async def get_coverage(
    service: DigitalTwinServiceDep,
    scenario_id: str | None = Query(default=None),
) -> CoverageResponse:
    try:
        cov = service.coverage(scenario_id)
    except ScenarioNotFoundError as exc:
        raise NotFoundError(f"Scenario not found: {scenario_id}") from exc
    except ScenarioApplicationError as exc:
        raise ValidationError(str(exc)) from exc
    return coverage_to_response(cov)


# ------------------------------------------------------------- optimization ---
@router.post("/placements", response_model=list[PlacementEvaluationView])
async def evaluate_placements(
    payload: PlacementRequest, service: DigitalTwinServiceDep
) -> list[PlacementEvaluationView]:
    candidates = [
        PlacementCandidate(id=c.id, name=c.name, x=c.x, y=c.y, units=c.units)
        for c in payload.candidates
    ]
    return [placement_to_view(e) for e in service.evaluate_placements(candidates)]


# ------------------------------------------------------------------ forecast ---
@router.post("/forecast", response_model=ForecastResponse)
async def forecast(
    payload: ForecastRequest, service: DigitalTwinServiceDep
) -> ForecastResponse:
    result = service.forecast(forecast_config_from_request(payload))
    return forecast_to_response(result)


# ------------------------------------------------------------------ reports ---
@router.get("/reports", response_model=ReportResponse)
async def get_reports(
    service: DigitalTwinServiceDep,
    scenario_id: list[str] | None = Query(default=None),
) -> ReportResponse:
    try:
        report = service.report(scenario_id)
    except ScenarioNotFoundError as exc:
        raise NotFoundError("Scenario not found") from exc
    except ScenarioApplicationError as exc:
        raise ValidationError(str(exc)) from exc
    return report_to_response(report)
