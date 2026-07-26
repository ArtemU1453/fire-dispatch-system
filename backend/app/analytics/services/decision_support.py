"""DecisionSupportService — analytical findings (stage §7).

Detects overloaded districts / units, long processing times and load trends and
returns **advisory findings only**. It never changes Dispatch-Engine
recommendations, incidents or any other data — it just surfaces insight for
management.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.analytics.repositories import AnalyticsRepository
from app.analytics.services.trends_service import TrendsService
from app.analytics.utils.period import Period


@dataclass(slots=True)
class Thresholds:
    overload_factor: float = 2.0       # x above the mean = overloaded
    min_district_incidents: int = 5
    min_unit_assignments: int = 5
    long_processing_seconds: float = 3600.0
    trend_change_pct: float = 25.0


@dataclass(slots=True)
class Finding:
    type: str
    severity: str  # info | warning | critical
    title: str
    detail: str
    value: float | None = None


@dataclass(slots=True)
class DecisionSupportResult:
    findings: list[Finding] = field(default_factory=list)


def _overloaded(rows, *, factor: float, floor: int) -> list[tuple[str, int]]:
    if not rows:
        return []
    mean = sum(c for _, c in rows) / len(rows)
    return [
        (label, count)
        for label, count in rows
        if count >= floor and count > factor * mean
    ]


class DecisionSupportService:
    def __init__(
        self, repo: AnalyticsRepository, thresholds: Thresholds | None = None
    ) -> None:
        self._repo = repo
        self._t = thresholds or Thresholds()
        self._trends = TrendsService(repo)

    async def analyze(self, period: Period) -> DecisionSupportResult:
        findings: list[Finding] = []

        # Overloaded districts.
        districts = await self._repo.district_distribution(period)
        for label, count in _overloaded(
            districts, factor=self._t.overload_factor,
            floor=self._t.min_district_incidents,
        ):
            findings.append(Finding(
                type="overloaded_district", severity="warning",
                title=f"Перегруженный район: {label}",
                detail=f"{count} происшествий за период — выше среднего",
                value=float(count),
            ))

        # Overloaded units.
        units = await self._repo.unit_load_distribution(period)
        for label, count in _overloaded(
            units, factor=self._t.overload_factor,
            floor=self._t.min_unit_assignments,
        ):
            findings.append(Finding(
                type="overloaded_unit", severity="warning",
                title=f"Перегруженное подразделение: {label}",
                detail=f"{count} назначений за период — выше среднего",
                value=float(count),
            ))

        # Long processing time.
        avg_proc = await self._repo.avg_processing_seconds(period)
        if avg_proc is not None and avg_proc > self._t.long_processing_seconds:
            findings.append(Finding(
                type="long_processing", severity="warning",
                title="Длительное время обработки",
                detail=(
                    f"Среднее время обработки {avg_proc / 60:.0f} мин "
                    "превышает порог"
                ),
                value=round(avg_proc, 1),
            ))

        # Rising-load trend.
        for trend in await self._trends.compute(
            period, keys=("calls_total", "incidents_total")
        ):
            if (
                trend.direction == "up"
                and trend.change_pct is not None
                and trend.change_pct >= self._t.trend_change_pct
            ):
                findings.append(Finding(
                    type="rising_load", severity="info",
                    title=f"Рост нагрузки: {trend.name}",
                    detail=(
                        f"Рост на {trend.change_pct:.0f}% "
                        "относительно прошлого периода"
                    ),
                    value=trend.change_pct,
                ))

        return DecisionSupportResult(findings=findings)
