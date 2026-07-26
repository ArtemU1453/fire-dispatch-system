"""ReportService — daily / weekly / monthly / custom reports (stage §5).

A report bundles the KPI set and statistics for a period. Long reports are
computed synchronously here; the architecture leaves a seam for background
computation / scheduling (stage §10) without a concrete task backend at this
stage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.kpi import KPIValue
from app.analytics.repositories import AnalyticsRepository
from app.analytics.services.kpi_service import KPIService
from app.analytics.statistics import StatisticsResult, StatisticsService
from app.analytics.utils.period import Period
from app.analytics.utils.rbac import AnalyticsAccess


@dataclass(slots=True)
class ReportResult:
    period: Period
    generated_at: datetime
    kpis: list[KPIValue] = field(default_factory=list)
    statistics: StatisticsResult | None = None


class ReportService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = AnalyticsRepository(session)
        self._access = AnalyticsAccess(session)
        self._kpi = KPIService(self._repo)
        self._stats = StatisticsService(self._repo)

    async def generate(
        self, period: Period, *, actor_id: UUID | None = None
    ) -> ReportResult:
        await self._access.require(actor_id, "analytics.view")
        return ReportResult(
            period=period,
            generated_at=datetime.now(tz=UTC),
            kpis=await self._kpi.compute(period),
            statistics=await self._stats.compute(period),
        )
