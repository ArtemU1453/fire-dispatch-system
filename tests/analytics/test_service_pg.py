"""Integration tests for analytics KPI / statistics computation (PostgreSQL)."""

from __future__ import annotations

import pytest

from app.analytics.dashboards import DashboardRole, DashboardService
from app.analytics.repositories import AnalyticsRepository
from app.analytics.services import KPIService
from app.analytics.statistics import StatisticsService
from app.analytics.utils.period import Period, PeriodKind

from .conftest import AnalyticsSeed

pytestmark = pytest.mark.asyncio
DAY = PeriodKind.DAY


def _kpi(values, key):
    return next(v for v in values if v.key == key)


async def test_kpi_values_are_correct(pg_factory, seed: AnalyticsSeed) -> None:
    async with pg_factory() as s:
        values = await KPIService(AnalyticsRepository(s)).compute(Period.of(DAY))
        assert _kpi(values, "calls_total").value == 3
        assert _kpi(values, "incidents_total").value == 3
        # wait times 10/20/30 → mean 20
        assert _kpi(values, "avg_call_registration_seconds").value == 20
        # 2 incidents confirmed 60s after report
        assert _kpi(values, "avg_decision_seconds").value == 60
        # first dispatch 120s after report
        assert _kpi(values, "avg_assignment_seconds").value == 120
        # 3 calls / 1 dispatcher
        assert _kpi(values, "dispatcher_load").value == 3
        # 2 assignments / 1 unit
        assert _kpi(values, "unit_load").value == 2
        # ETA is intentionally unavailable
        assert _kpi(values, "avg_eta_seconds").value is None


async def test_statistics(pg_factory, seed: AnalyticsSeed) -> None:
    async with pg_factory() as s:
        stats = await StatisticsService(AnalyticsRepository(s)).compute(
            Period.of(DAY)
        )
        types = {d.label: d.count for d in stats.by_incident_type}
        assert types.get(seed.incident_type_name) == 3
        districts = {d.label: d.count for d in stats.by_district}
        assert districts.get(seed.area_name) == 3
        assert sum(d.count for d in stats.call_dynamics) == 3
        # 1 incident had 1 dispatch → avg units per incident = 1
        assert stats.avg_units_per_incident == 1


async def test_period_scopes_results(pg_factory, seed: AnalyticsSeed) -> None:
    async with pg_factory() as s:
        repo = AnalyticsRepository(s)
        # A window entirely before the seed data has no calls.
        empty = await repo.call_count(Period.of(DAY).previous())
        assert empty == 0
        assert await repo.call_count(Period.of(DAY)) == 3


async def test_dashboard_roles(pg_factory, seed: AnalyticsSeed) -> None:
    async with pg_factory() as s:
        svc = DashboardService(s)
        lead = await svc.build(DashboardRole.SHIFT_LEAD, Period.of(DAY))
        assert lead.statistics is not None
        keys = {k.key for k in lead.kpis}
        assert "calls_total" in keys and "avg_eta_seconds" not in keys

        dispatcher = await svc.build(DashboardRole.DISPATCHER, Period.of(DAY))
        assert dispatcher.statistics is None  # dispatcher view is KPI-only

        admin = await svc.build(DashboardRole.ADMIN, Period.of(DAY))
        # admin sees the full KPI set
        assert len(admin.kpis) >= 10
        assert admin.trends
