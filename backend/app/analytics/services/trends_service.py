"""TrendsService — compares a KPI's current window to the previous one.

Purely descriptive (no forecasting — stage constraint): it reports the direction
and magnitude of change between two equal, adjacent windows.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.analytics.kpi import DEFAULT_KPIS, KPIRegistry
from app.analytics.repositories import AnalyticsRepository
from app.analytics.utils.period import Period

_DEFAULT_TREND_KPIS = (
    "calls_total", "incidents_total", "avg_decision_seconds",
    "avg_assignment_seconds", "dispatcher_load", "unit_load",
)


@dataclass(slots=True)
class Trend:
    key: str
    name: str
    unit: str
    current: float | None
    previous: float | None
    change_pct: float | None
    direction: str  # up | down | flat | n/a


def _direction(
    current: float | None, previous: float | None
) -> tuple[str, float | None]:
    if current is None or previous is None:
        return "n/a", None
    if previous == 0:
        return ("up" if current > 0 else "flat"), None
    change = round(100.0 * (current - previous) / previous, 1)
    if abs(change) < 1.0:
        return "flat", change
    return ("up" if change > 0 else "down"), change


class TrendsService:
    def __init__(
        self, repo: AnalyticsRepository, registry: KPIRegistry | None = None
    ) -> None:
        self._repo = repo
        self._registry = registry or DEFAULT_KPIS

    async def compute(
        self, period: Period, *, keys: Sequence[str] | None = None
    ) -> list[Trend]:
        previous = period.previous()
        selected = keys or _DEFAULT_TREND_KPIS
        trends: list[Trend] = []
        for key in selected:
            kpi = self._registry.get(key)
            if kpi is None:
                continue
            current = await kpi.compute(self._repo, period)
            prior = await kpi.compute(self._repo, previous)
            direction, change = _direction(current, prior)
            trends.append(
                Trend(
                    key=kpi.key, name=kpi.name, unit=kpi.unit,
                    current=round(current, 2) if current is not None else None,
                    previous=round(prior, 2) if prior is not None else None,
                    change_pct=change, direction=direction,
                )
            )
        return trends
