"""Mapping between analytics dataclasses and API schemas."""

from __future__ import annotations

from app.analytics.dashboards.service import DashboardResult
from app.analytics.kpi import KPIValue
from app.analytics.reports.service import ReportResult
from app.analytics.schemas.analytics import (
    DashboardResponse,
    DistributionItem,
    FindingResponse,
    KPIResponse,
    PeriodInfo,
    ReportResponse,
    StatisticsResponse,
    TrendResponse,
)
from app.analytics.services.decision_support import Finding
from app.analytics.services.trends_service import Trend
from app.analytics.statistics import Distribution, StatisticsResult
from app.analytics.utils.period import Period


def period_info(period: Period) -> PeriodInfo:
    return PeriodInfo(kind=period.kind, start=period.start, end=period.end)


def kpi_to_response(v: KPIValue) -> KPIResponse:
    return KPIResponse(
        key=v.key, name=v.name, value=v.value, unit=v.unit,
        description=v.description, category=v.category,
    )


def _dist(d: Distribution) -> DistributionItem:
    return DistributionItem(label=d.label, count=d.count)


def statistics_to_response(
    period: Period, stats: StatisticsResult
) -> StatisticsResponse:
    return StatisticsResponse(
        period=period_info(period),
        by_incident_type=[_dist(d) for d in stats.by_incident_type],
        by_district=[_dist(d) for d in stats.by_district],
        unit_load=[_dist(d) for d in stats.unit_load],
        call_dynamics=[_dist(d) for d in stats.call_dynamics],
        avg_units_per_incident=stats.avg_units_per_incident,
        avg_processing_seconds=stats.avg_processing_seconds,
        recommendation_change_frequency=stats.recommendation_change_frequency,
    )


def finding_to_response(f: Finding) -> FindingResponse:
    return FindingResponse(
        type=f.type, severity=f.severity, title=f.title,
        detail=f.detail, value=f.value,
    )


def trend_to_response(t: Trend) -> TrendResponse:
    return TrendResponse(
        key=t.key, name=t.name, unit=t.unit, current=t.current,
        previous=t.previous, change_pct=t.change_pct, direction=t.direction,
    )


def dashboard_to_response(
    period: Period, result: DashboardResult
) -> DashboardResponse:
    return DashboardResponse(
        role=result.role, title=result.title, period=period_info(period),
        kpis=[kpi_to_response(v) for v in result.kpis],
        statistics=(
            statistics_to_response(period, result.statistics)
            if result.statistics is not None
            else None
        ),
        findings=[finding_to_response(f) for f in result.findings],
        trends=[trend_to_response(t) for t in result.trends],
    )


def report_to_response(result: ReportResult) -> ReportResponse:
    return ReportResponse(
        period=period_info(result.period),
        generated_at=result.generated_at,
        kpis=[kpi_to_response(v) for v in result.kpis],
        statistics=(
            statistics_to_response(result.period, result.statistics)
            if result.statistics is not None
            else None
        ),
    )
