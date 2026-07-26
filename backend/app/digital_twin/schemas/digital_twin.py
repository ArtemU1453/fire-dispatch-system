"""Pydantic schemas for the Digital Twin REST API (Stage 18 §8)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# --------------------------------------------------------------- scenarios ---
class ModificationSchema(BaseModel):
    type: str
    params: dict[str, Any] = Field(default_factory=dict)
    note: str = ""


class ScenarioSummary(BaseModel):
    id: str
    title: str
    description: str
    objectives: list[str]
    modification_count: int


class ScenarioDetail(BaseModel):
    id: str
    title: str
    description: str = ""
    objectives: list[str] = Field(default_factory=list)
    modifications: list[ModificationSchema] = Field(default_factory=list)
    format_version: int = 1


class ScenarioCreate(BaseModel):
    id: str
    title: str
    description: str = ""
    objectives: list[str] = Field(default_factory=list)
    modifications: list[ModificationSchema] = Field(default_factory=list)


# ---------------------------------------------------------------- coverage ---
class DistrictCoverageView(BaseModel):
    district_id: str
    name: str
    nearest_station_id: str | None
    arrival_time_s: float | None
    covered: bool
    responders_in_norm: int


class CoverageResponse(BaseModel):
    territory_covered_pct: float
    population_covered_pct: float
    avg_arrival_time_s: float | None
    unreachable_districts: list[str]
    risk_zones: list[str]
    overlap_pct: float
    grid_size: int
    per_district: list[DistrictCoverageView]


# ---------------------------------------------------------------- simulate ---
class SimulateRequest(BaseModel):
    scenario_id: str


class ImpactView(BaseModel):
    scenario_id: str
    delta_population_pct: float
    delta_territory_pct: float
    newly_covered_districts: list[str]
    newly_uncovered_districts: list[str]
    verdict: str


class SimulationResultView(BaseModel):
    id: str
    scenario_id: str
    scenario_title: str
    created_at: str
    baseline: CoverageResponse
    scenario: CoverageResponse
    impact: ImpactView


# ------------------------------------------------------------- optimization ---
class PlacementCandidateSchema(BaseModel):
    id: str
    name: str
    x: float
    y: float
    units: int = 1


class PlacementRequest(BaseModel):
    candidates: list[PlacementCandidateSchema]


class PlacementEvaluationView(BaseModel):
    candidate_id: str
    name: str
    x: float
    y: float
    population_covered_pct: float
    territory_covered_pct: float
    delta_population_pct: float
    delta_territory_pct: float
    unreachable_after: list[str]


# ---------------------------------------------------------------- forecast ---
class ForecastRequest(BaseModel):
    horizon_years: int = Field(default=5, ge=0, le=50)
    call_growth_rate: float = 0.04
    population_growth_rate: float = 0.02
    accessibility_change_rate: float = 0.0
    compound: bool = False


class ProjectionPointView(BaseModel):
    year: int
    value: float


class ForecastResponse(BaseModel):
    horizon_years: int
    calls_per_day: list[ProjectionPointView]
    population_total: list[ProjectionPointView]
    accessibility_multiplier: list[ProjectionPointView]
    notes: list[str]


# ----------------------------------------------------------------- reports ---
class ReportResponse(BaseModel):
    baseline: dict[str, Any]
    coverage_map: dict[str, Any]
    risk_map: dict[str, Any]
    scenario_comparison: list[dict[str, Any]]
    impact: list[dict[str, Any]]
    justification: list[str]
