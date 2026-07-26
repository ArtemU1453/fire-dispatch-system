"""KPI definitions and the extensible registry (stage §3).

A KPI is a small descriptor bundling a key, human name, unit and an async
``compute`` function over the analytics repository and a period. New KPIs are
added by **registering** a new ``KPI`` (in this or any other module) — no existing
code changes, satisfying "add new KPIs without changing existing code".
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from app.analytics.repositories.analytics_repository import AnalyticsRepository
from app.analytics.utils.period import Period

ComputeFn = Callable[[AnalyticsRepository, Period], Awaitable[float | None]]


@dataclass(slots=True)
class KPI:
    key: str
    name: str
    unit: str
    compute: ComputeFn
    description: str = ""
    category: str = "general"


@dataclass(slots=True)
class KPIValue:
    key: str
    name: str
    value: float | None
    unit: str
    description: str
    category: str


class KPIRegistry:
    """An ordered collection of KPIs, keyed by ``key``."""

    def __init__(self) -> None:
        self._kpis: dict[str, KPI] = {}

    def register(self, kpi: KPI) -> KPI:
        self._kpis[kpi.key] = kpi
        return kpi

    def get(self, key: str) -> KPI | None:
        return self._kpis.get(key)

    def keys(self) -> list[str]:
        return list(self._kpis.keys())

    def all(self) -> list[KPI]:
        return list(self._kpis.values())

    async def compute(
        self, kpi: KPI, repo: AnalyticsRepository, period: Period
    ) -> KPIValue:
        value = await kpi.compute(repo, period)
        return KPIValue(
            key=kpi.key, name=kpi.name,
            value=round(value, 2) if value is not None else None,
            unit=kpi.unit, description=kpi.description, category=kpi.category,
        )
