"""Map Digital Twin domain objects to API schemas (Stage 18 §8)."""

from __future__ import annotations

from app.digital_twin.coverage.analyzer import CoverageResult
from app.digital_twin.forecast.service import ForecastResult
from app.digital_twin.optimization.optimizer import PlacementEvaluation
from app.digital_twin.planning.service import SimulationResult
from app.digital_twin.reports.report_builder import AnalyticalReport
from app.digital_twin.scenarios.schema import Modification, Scenario
from app.digital_twin.schemas.digital_twin import (
    CoverageResponse,
    ForecastRequest,
    ForecastResponse,
    PlacementEvaluationView,
    ReportResponse,
    ScenarioCreate,
    ScenarioDetail,
    ScenarioSummary,
    SimulationResultView,
)


def scenario_to_summary(s: Scenario) -> ScenarioSummary:
    return ScenarioSummary(
        id=s.id,
        title=s.title,
        description=s.description,
        objectives=list(s.objectives),
        modification_count=len(s.modifications),
    )


def scenario_to_detail(s: Scenario) -> ScenarioDetail:
    return ScenarioDetail.model_validate(s.to_dict())


def scenario_from_create(payload: ScenarioCreate) -> Scenario:
    return Scenario(
        id=payload.id,
        title=payload.title,
        description=payload.description,
        objectives=list(payload.objectives),
        modifications=[
            Modification(type=m.type, params=dict(m.params), note=m.note)
            for m in payload.modifications
        ],
    )


def coverage_to_response(cov: CoverageResult) -> CoverageResponse:
    return CoverageResponse.model_validate(cov.to_dict())


def simulation_result_to_view(result: SimulationResult) -> SimulationResultView:
    return SimulationResultView(
        id=result.id,
        scenario_id=result.scenario_id,
        scenario_title=result.scenario_title,
        created_at=result.created_at.isoformat(),
        baseline=CoverageResponse.model_validate(result.baseline),
        scenario=CoverageResponse.model_validate(result.scenario),
        impact=result.impact,
    )


def placement_to_view(e: PlacementEvaluation) -> PlacementEvaluationView:
    return PlacementEvaluationView(**e.__dict__)


def forecast_config_from_request(req: ForecastRequest):
    from app.digital_twin.forecast.service import ForecastConfig

    return ForecastConfig(
        horizon_years=req.horizon_years,
        call_growth_rate=req.call_growth_rate,
        population_growth_rate=req.population_growth_rate,
        accessibility_change_rate=req.accessibility_change_rate,
        compound=req.compound,
    )


def forecast_to_response(result: ForecastResult) -> ForecastResponse:
    return ForecastResponse.model_validate(result.to_dict())


def report_to_response(report: AnalyticalReport) -> ReportResponse:
    return ReportResponse(
        baseline=report.baseline,
        coverage_map=report.coverage_map,
        risk_map=report.risk_map,
        scenario_comparison=report.scenario_comparison,
        impact=report.impact,
        justification=report.justification,
    )
