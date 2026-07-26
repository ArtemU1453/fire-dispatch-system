"""DashboardService — the aggregated system status (stage §7).

Combines health, key metrics and freshly-evaluated alerts into one summary for
``GET /observability/status``.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.observability.alerts import AlertService
from app.observability.health import HealthService, HealthState
from app.observability.services.metrics_service import MetricsService
from app.observability.state import alert_registry, uptime_seconds


@dataclass(slots=True)
class ComponentSummary:
    component: str
    state: HealthState


@dataclass(slots=True)
class DashboardSummary:
    state: HealthState
    version: str
    uptime_seconds: float
    components: list[ComponentSummary]
    key_metrics: dict[str, float]
    active_alerts: int


class DashboardService:
    def __init__(
        self, session: AsyncSession, settings: Settings | None = None
    ) -> None:
        self._settings = settings or get_settings()
        self._health = HealthService(session, self._settings)
        self._metrics = MetricsService(session)
        self._alerts = AlertService(alert_registry)

    async def status(self) -> DashboardSummary:
        report = await self._health.report()
        gauges = await self._metrics.refresh_business()
        alerts = self._alerts.evaluate(report.components, self._metrics.registry)
        return DashboardSummary(
            state=report.state,
            version=report.version,
            uptime_seconds=uptime_seconds(),
            components=[
                ComponentSummary(component=c.component, state=c.state)
                for c in report.components
            ],
            key_metrics={
                "active_incidents": gauges.get("active_incidents", 0.0),
                "active_calls": gauges.get("active_calls", 0.0),
                "available_units": gauges.get("available_units", 0.0),
                "call_queue_size": gauges.get("call_queue_size", 0.0),
                "active_users": gauges.get("active_users", 0.0),
            },
            active_alerts=len(alerts),
        )
