"""Pydantic schemas for the simulation & training REST API (Stage 17 §9)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# --------------------------------------------------------------- scenarios ---
class ScenarioUnitSchema(BaseModel):
    id: str
    name: str
    category: str
    x: float
    y: float
    speed_kmh: float = 50.0


class ScenarioEventSchema(BaseModel):
    time_s: float
    type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    id: str = ""


class EvaluationCriteriaSchema(BaseModel):
    max_response_time_s: float = 120.0
    min_correct_pct: float = 80.0
    max_errors: int = 2
    max_decision_changes: int = 3
    pass_score: float = 70.0


class ExpectedResultSchema(BaseModel):
    resolved_incidents: int = 0
    max_expired_incidents: int = 0
    notes: str = ""


class ScenarioSummary(BaseModel):
    id: str
    title: str
    description: str
    mode: str
    objectives: list[str]
    duration_s: float
    unit_count: int
    event_count: int


class ScenarioDetail(BaseModel):
    id: str
    title: str
    description: str
    mode: str
    objectives: list[str] = Field(default_factory=list)
    seed: int = 0
    duration_s: float = 1800.0
    units: list[ScenarioUnitSchema] = Field(default_factory=list)
    events: list[ScenarioEventSchema] = Field(default_factory=list)
    expected: ExpectedResultSchema = Field(default_factory=ExpectedResultSchema)
    criteria: EvaluationCriteriaSchema = Field(default_factory=EvaluationCriteriaSchema)
    format_version: int = 1


class ScenarioCreate(BaseModel):
    id: str
    title: str
    description: str = ""
    mode: str = "training"
    objectives: list[str] = Field(default_factory=list)
    seed: int = 0
    duration_s: float = 1800.0
    units: list[ScenarioUnitSchema] = Field(default_factory=list)
    events: list[ScenarioEventSchema] = Field(default_factory=list)
    expected: ExpectedResultSchema = Field(default_factory=ExpectedResultSchema)
    criteria: EvaluationCriteriaSchema = Field(default_factory=EvaluationCriteriaSchema)


# ---------------------------------------------------------------- sessions ---
class StartRequest(BaseModel):
    scenario_id: str
    trainee: str = "trainee"
    speed: float = Field(default=1.0, gt=0)
    mode: str | None = None


class StopRequest(BaseModel):
    session_id: str


class DispatchRequest(BaseModel):
    incident_id: str
    unit_ids: list[str] = Field(default_factory=list)


class ResolveRequest(BaseModel):
    incident_id: str


class ControlRequest(BaseModel):
    op: str = Field(description="pause | resume | step | advance | set_speed")
    seconds: float | None = Field(default=None, ge=0)
    speed: float | None = Field(default=None, gt=0)


class IncidentView(BaseModel):
    id: str
    type: str
    x: float
    y: float
    severity: int
    status: str
    required_units: int
    required_category: str
    dispatched_unit_ids: list[str] = Field(default_factory=list)
    is_false_alarm: bool = False
    label: str = ""


class UnitView(BaseModel):
    id: str
    name: str
    category: str
    status: str
    x: float
    y: float
    assigned_incident_id: str | None = None


class SessionResponse(BaseModel):
    id: str
    scenario_id: str
    trainee: str
    mode: str
    state: str
    sim_time_s: float
    speed: float
    paused: bool
    weather: str
    closed_roads: list[str] = Field(default_factory=list)
    incidents: list[IncidentView] = Field(default_factory=list)
    units: list[UnitView] = Field(default_factory=list)


class ActionResponse(BaseModel):
    accepted: bool
    message: str
    incident_id: str | None = None


# ----------------------------------------------------------------- results ---
class IncidentEvaluationView(BaseModel):
    incident_id: str
    is_false_alarm: bool
    reaction_time_s: float | None
    within_norm: bool
    correct: bool
    resolved: bool


class ReportResponse(BaseModel):
    session_id: str
    scenario_id: str
    scenario_title: str
    mode: str
    trainee: str
    verdict: str
    score: float
    metrics: dict[str, Any]
    objectives: list[str] = Field(default_factory=list)
    per_incident: list[IncidentEvaluationView] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class StatisticsResponse(BaseModel):
    sessions_total: int
    sessions_completed: int
    passed: int
    failed: int
    pass_rate_pct: float
    avg_score: float
    by_scenario: dict[str, int]
