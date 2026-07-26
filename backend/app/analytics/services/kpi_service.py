"""KPIService — computes KPI values over a period via the registry."""

from __future__ import annotations

from collections.abc import Sequence

from app.analytics.kpi import DEFAULT_KPIS, KPIRegistry, KPIValue
from app.analytics.repositories import AnalyticsRepository
from app.analytics.utils.period import Period


class KPIService:
    def __init__(
        self, repo: AnalyticsRepository, registry: KPIRegistry | None = None
    ) -> None:
        self._repo = repo
        self._registry = registry or DEFAULT_KPIS

    async def compute(
        self, period: Period, *, keys: Sequence[str] | None = None
    ) -> list[KPIValue]:
        kpis = (
            [k for key in keys if (k := self._registry.get(key))]
            if keys is not None
            else self._registry.all()
        )
        return [
            await self._registry.compute(kpi, self._repo, period) for kpi in kpis
        ]

    @property
    def registry(self) -> KPIRegistry:
        return self._registry
