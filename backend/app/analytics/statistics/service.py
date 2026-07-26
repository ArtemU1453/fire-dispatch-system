"""StatisticsService — operational distributions and averages (stage §6)."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.analytics.repositories import AnalyticsRepository
from app.analytics.utils.period import Period


@dataclass(slots=True)
class Distribution:
    label: str
    count: int


@dataclass(slots=True)
class StatisticsResult:
    by_incident_type: list[Distribution] = field(default_factory=list)
    by_district: list[Distribution] = field(default_factory=list)
    unit_load: list[Distribution] = field(default_factory=list)
    call_dynamics: list[Distribution] = field(default_factory=list)
    avg_units_per_incident: float | None = None
    avg_processing_seconds: float | None = None
    recommendation_change_frequency: float | None = None


def _dist(rows: list[tuple[str, int]]) -> list[Distribution]:
    return [Distribution(label=label, count=count) for label, count in rows]


class StatisticsService:
    def __init__(self, repo: AnalyticsRepository) -> None:
        self._repo = repo

    async def compute(self, period: Period) -> StatisticsResult:
        return StatisticsResult(
            by_incident_type=_dist(
                await self._repo.incident_type_distribution(period)
            ),
            by_district=_dist(await self._repo.district_distribution(period)),
            unit_load=_dist(await self._repo.unit_load_distribution(period)),
            call_dynamics=_dist(await self._repo.call_dynamics(period)),
            avg_units_per_incident=await self._repo.avg_units_per_incident(period),
            avg_processing_seconds=await self._repo.avg_processing_seconds(period),
            recommendation_change_frequency=(
                await self._repo.recommendation_change_frequency(period)
            ),
        )
