"""Analytics REST endpoints (stage §8).

    GET  /analytics/kpi          · /statistics · /trends
    GET  /analytics/dashboard/{role} · /reports · /decision-support
    POST /analytics/export

All reads honour RBAC when a user is identified (``actor_id``); export is
additionally audited. Aggregated reads are cached briefly.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, Response

from app.analytics.dashboards import DashboardRole, DashboardService
from app.analytics.deps import AnalyticsAccessDep, AnalyticsRepoDep, PeriodDep
from app.analytics.reports import ReportService
from app.analytics.schemas.analytics import (
    DashboardResponse,
    ExportRequest,
    FindingResponse,
    KPIReportResponse,
    ReportResponse,
    StatisticsResponse,
    TrendReportResponse,
)
from app.analytics.services import (
    DecisionSupportService,
    ExportService,
    KPIService,
    TrendsService,
)
from app.analytics.statistics import StatisticsService
from app.analytics.utils.cache import analytics_cache
from app.analytics.utils.mapping import (
    dashboard_to_response,
    finding_to_response,
    kpi_to_response,
    period_info,
    report_to_response,
    statistics_to_response,
    trend_to_response,
)
from app.analytics.utils.period import Period
from app.api.deps import SessionDep

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _key(prefix: str, period: Period) -> str:
    return f"{prefix}:{period.start.isoformat()}:{period.end.isoformat()}"


@router.get("/kpi", response_model=KPIReportResponse, summary="KPI report")
async def get_kpi(
    repo: AnalyticsRepoDep,
    access: AnalyticsAccessDep,
    period: PeriodDep,
    actor_id: UUID | None = Query(default=None),
) -> KPIReportResponse:
    await access.require(actor_id, "analytics.view")
    values = await analytics_cache.get_or_compute(
        _key("kpi", period), lambda: KPIService(repo).compute(period)
    )
    return KPIReportResponse(
        period=period_info(period),
        kpis=[kpi_to_response(v) for v in values],
    )


@router.get("/statistics", response_model=StatisticsResponse, summary="Statistics")
async def get_statistics(
    repo: AnalyticsRepoDep,
    access: AnalyticsAccessDep,
    period: PeriodDep,
    actor_id: UUID | None = Query(default=None),
) -> StatisticsResponse:
    await access.require(actor_id, "analytics.view")
    stats = await analytics_cache.get_or_compute(
        _key("stats", period), lambda: StatisticsService(repo).compute(period)
    )
    return statistics_to_response(period, stats)


@router.get("/trends", response_model=TrendReportResponse, summary="Trends")
async def get_trends(
    repo: AnalyticsRepoDep,
    access: AnalyticsAccessDep,
    period: PeriodDep,
    actor_id: UUID | None = Query(default=None),
) -> TrendReportResponse:
    await access.require(actor_id, "analytics.view")
    trends = await analytics_cache.get_or_compute(
        _key("trends", period), lambda: TrendsService(repo).compute(period)
    )
    return TrendReportResponse(
        period=period_info(period),
        trends=[trend_to_response(t) for t in trends],
    )


@router.get(
    "/decision-support", response_model=list[FindingResponse],
    summary="Decision-support findings",
)
async def get_findings(
    repo: AnalyticsRepoDep,
    access: AnalyticsAccessDep,
    period: PeriodDep,
    actor_id: UUID | None = Query(default=None),
) -> list[FindingResponse]:
    await access.require(actor_id, "analytics.view")
    result = await DecisionSupportService(repo).analyze(period)
    return [finding_to_response(f) for f in result.findings]


@router.get(
    "/dashboard/{role}", response_model=DashboardResponse,
    summary="Role dashboard",
)
async def get_dashboard(
    session: SessionDep,
    role: DashboardRole,
    period: PeriodDep,
    actor_id: UUID | None = Query(default=None),
) -> DashboardResponse:
    result = await DashboardService(session).build(
        role, period, actor_id=actor_id
    )
    return dashboard_to_response(period, result)


@router.get(
    "/reports", response_model=ReportResponse, summary="Generate a report"
)
async def get_report(
    session: SessionDep,
    period: PeriodDep,
    actor_id: UUID | None = Query(default=None),
) -> ReportResponse:
    result = await ReportService(session).generate(period, actor_id=actor_id)
    return report_to_response(result)


@router.post("/export", summary="Export an analytics dataset (CSV / XLSX)")
async def export(session: SessionDep, data: ExportRequest) -> Response:
    period = Period.of(data.period, start=data.start, end=data.end)
    result = await ExportService(session).export(
        data.dataset, data.format, period,
        actor_id=data.actor_id, actor_name=data.actor_name,
    )
    return Response(
        content=result.content,
        media_type=result.media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"'
        },
    )
