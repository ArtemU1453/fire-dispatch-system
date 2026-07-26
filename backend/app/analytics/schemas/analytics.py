"""Pydantic schemas for the analytics platform (stage §9)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.analytics.dashboards.policy import DashboardRole
from app.analytics.export.formats import ExportFormat
from app.analytics.utils.period import PeriodKind
from app.schemas.common import SchemaBase


class PeriodInfo(SchemaBase):
    kind: PeriodKind
    start: datetime
    end: datetime


class KPIResponse(SchemaBase):
    key: str
    name: str
    value: float | None = None
    unit: str
    description: str = ""
    category: str = "general"


class KPIReportResponse(SchemaBase):
    period: PeriodInfo
    kpis: list[KPIResponse] = []


class DistributionItem(SchemaBase):
    label: str
    count: int


class StatisticsResponse(SchemaBase):
    period: PeriodInfo
    by_incident_type: list[DistributionItem] = []
    by_district: list[DistributionItem] = []
    unit_load: list[DistributionItem] = []
    call_dynamics: list[DistributionItem] = []
    avg_units_per_incident: float | None = None
    avg_processing_seconds: float | None = None
    recommendation_change_frequency: float | None = None


class FindingResponse(SchemaBase):
    type: str
    severity: str
    title: str
    detail: str
    value: float | None = None


class TrendResponse(SchemaBase):
    key: str
    name: str
    unit: str
    current: float | None = None
    previous: float | None = None
    change_pct: float | None = None
    direction: str


class TrendReportResponse(SchemaBase):
    period: PeriodInfo
    trends: list[TrendResponse] = []


class DashboardResponse(SchemaBase):
    role: DashboardRole
    title: str
    period: PeriodInfo
    kpis: list[KPIResponse] = []
    statistics: StatisticsResponse | None = None
    findings: list[FindingResponse] = []
    trends: list[TrendResponse] = []


class ReportResponse(SchemaBase):
    period: PeriodInfo
    generated_at: datetime
    kpis: list[KPIResponse] = []
    statistics: StatisticsResponse | None = None


class ExportRequest(SchemaBase):
    dataset: str = "kpi"
    format: ExportFormat = ExportFormat.CSV
    period: PeriodKind = PeriodKind.DAY
    start: datetime | None = None
    end: datetime | None = None
    actor_id: UUID | None = None
    actor_name: str | None = None
