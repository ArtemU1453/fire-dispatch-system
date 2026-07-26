"""Integration tests for observability services (require PostgreSQL)."""

from __future__ import annotations

import pytest

from app.observability.health import HealthService, HealthState
from app.observability.services import DashboardService, MetricsService

pytestmark = pytest.mark.asyncio


async def test_health_service_reports_components(pg_factory) -> None:
    async with pg_factory() as s:
        report = await HealthService(s).report()
        names = {c.component for c in report.components}
        assert "database" in names
        assert "incidents" in names and "calls" in names
        db = next(c for c in report.components if c.component == "database")
        assert db.state is HealthState.HEALTHY
        assert db.ready is True
        # overall state healthy (all probes ok against a migrated DB)
        assert report.state in (HealthState.HEALTHY, HealthState.DEGRADED)
        assert report.alive is True


async def test_metrics_service_collects_business_gauges(pg_factory) -> None:
    async with pg_factory() as s:
        gauges = await MetricsService(s).refresh_business()
        for key in (
            "active_incidents", "active_calls", "available_units",
            "call_queue_size", "active_users",
        ):
            assert key in gauges
            assert gauges[key] >= 0
        samples = await MetricsService(s).snapshot()
        names = {m.name for m in samples}
        assert "active_incidents" in names
        assert "service_uptime_seconds" in names


async def test_dashboard_status(pg_factory) -> None:
    async with pg_factory() as s:
        summary = await DashboardService(s).status()
        assert summary.version
        assert summary.uptime_seconds >= 0
        assert "active_incidents" in summary.key_metrics
        assert {c.component for c in summary.components} >= {"database", "calls"}
