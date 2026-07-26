"""MetricsService — refreshes business gauges and snapshots all metrics."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.observability.collectors import BusinessMetricsCollector
from app.observability.metrics import MetricSample, MetricsRegistry
from app.observability.state import metrics_registry, uptime_seconds

_COUNT_GAUGES = (
    "active_incidents", "active_calls", "available_units",
    "call_queue_size", "active_users",
)


class MetricsService:
    def __init__(
        self, session: AsyncSession, registry: MetricsRegistry | None = None
    ) -> None:
        self._session = session
        self._registry = registry or metrics_registry
        self._collector = BusinessMetricsCollector(session)

    async def refresh_business(self) -> dict[str, float]:
        """Collect business gauges into the registry and return them."""
        gauges = await self._collector.collect()
        for name, value in gauges.items():
            self._registry.set_gauge(name, value, unit="count")
        self._registry.set_gauge(
            "service_uptime_seconds", uptime_seconds(), unit="s"
        )
        return gauges

    async def snapshot(self) -> list[MetricSample]:
        await self.refresh_business()
        return self._registry.snapshot()

    @property
    def registry(self) -> MetricsRegistry:
        return self._registry
