"""Map simulator domain objects to API schemas (Stage 17 §9)."""

from __future__ import annotations

from app.simulator.reports.report_builder import TrainingReport
from app.simulator.scenarios.schema import (
    EvaluationCriteria,
    ExpectedResult,
    Scenario,
    ScenarioEvent,
    ScenarioUnit,
)
from app.simulator.schemas.simulator import (
    IncidentEvaluationView,
    IncidentView,
    ReportResponse,
    ScenarioCreate,
    ScenarioDetail,
    ScenarioSummary,
    SessionResponse,
    UnitView,
)
from app.simulator.services.session import TrainingSession


def scenario_to_summary(s: Scenario) -> ScenarioSummary:
    return ScenarioSummary(
        id=s.id,
        title=s.title,
        description=s.description,
        mode=s.mode,
        objectives=list(s.objectives),
        duration_s=s.duration_s,
        unit_count=len(s.units),
        event_count=len(s.events),
    )


def scenario_to_detail(s: Scenario) -> ScenarioDetail:
    return ScenarioDetail.model_validate(s.to_dict())


def scenario_from_create(payload: ScenarioCreate) -> Scenario:
    return Scenario(
        id=payload.id,
        title=payload.title,
        description=payload.description,
        mode=payload.mode,
        objectives=list(payload.objectives),
        seed=payload.seed,
        duration_s=payload.duration_s,
        units=[ScenarioUnit(**u.model_dump()) for u in payload.units],
        events=[ScenarioEvent(**e.model_dump()) for e in payload.events],
        expected=ExpectedResult(**payload.expected.model_dump()),
        criteria=EvaluationCriteria(**payload.criteria.model_dump()),
    )


def session_to_response(session: TrainingSession) -> SessionResponse:
    eng = session.engine
    incidents = [
        IncidentView(
            id=i.id,
            type=i.type.value,
            x=i.x,
            y=i.y,
            severity=i.severity,
            status=i.status.value,
            required_units=i.required_units,
            required_category=i.required_category.value,
            dispatched_unit_ids=list(i.dispatched_unit_ids),
            is_false_alarm=i.is_false_alarm,
            label=i.label,
        )
        for i in eng.world.incidents.values()
    ]
    units = [
        UnitView(
            id=u.id,
            name=u.name,
            category=u.category.value,
            status=u.status.value,
            x=u.x,
            y=u.y,
            assigned_incident_id=u.assigned_incident_id,
        )
        for u in eng.world.units.values()
    ]
    return SessionResponse(
        id=session.id,
        scenario_id=session.scenario.id,
        trainee=session.trainee,
        mode=session.mode,
        state=session.state.value,
        sim_time_s=round(eng.clock.time_s, 1),
        speed=eng.clock.speed,
        paused=eng.clock.paused,
        weather=eng.world.weather.value,
        closed_roads=sorted(eng.world.closed_roads),
        incidents=incidents,
        units=units,
    )


def report_to_response(report: TrainingReport) -> ReportResponse:
    return ReportResponse(
        session_id=report.session_id,
        scenario_id=report.scenario_id,
        scenario_title=report.scenario_title,
        mode=report.mode,
        trainee=report.trainee,
        verdict=report.verdict,
        score=report.score,
        metrics=report.metrics,
        objectives=list(report.objectives),
        per_incident=[IncidentEvaluationView(**ie) for ie in report.per_incident],
        recommendations=list(report.recommendations),
    )
