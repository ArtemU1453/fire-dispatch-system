"""DashboardService — assembles a role-specific analytics dashboard (stage §4)."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.dashboards.policy import DashboardRole, spec_for
from app.analytics.kpi import KPIValue
from app.analytics.repositories import AnalyticsRepository
from app.analytics.services.decision_support import (
    DecisionSupportService,
    Finding,
)
from app.analytics.services.kpi_service import KPIService
from app.analytics.services.trends_service import Trend, TrendsService
from app.analytics.statistics import StatisticsResult, StatisticsService
from app.analytics.utils.period import Period
from app.analytics.utils.rbac import AnalyticsAccess


@dataclass(slots=True)
class DashboardResult:
    role: DashboardRole
    title: str
    kpis: list[KPIValue] = field(default_factory=list)
    statistics: StatisticsResult | None = None
    findings: list[Finding] = field(default_factory=list)
    trends: list[Trend] = field(default_factory=list)


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = AnalyticsRepository(session)
        self._access = AnalyticsAccess(session)
        self._kpi = KPIService(self._repo)
        self._stats = StatisticsService(self._repo)
        self._findings = DecisionSupportService(self._repo)
        self._trends = TrendsService(self._repo)

    async def build(
        self,
        role: DashboardRole,
        period: Period,
        *,
        actor_id: UUID | None = None,
    ) -> DashboardResult:
        spec = spec_for(role)
        await self._access.require(actor_id, spec.required_permission)

        kpis = await self._kpi.compute(
            period, keys=spec.kpi_keys or None
        )
        statistics = (
            await self._stats.compute(period) if spec.include_statistics else None
        )
        findings = (
            (await self._findings.analyze(period)).findings
            if spec.include_findings
            else []
        )
        trends = (
            await self._trends.compute(period) if spec.include_trends else []
        )
        return DashboardResult(
            role=role, title=spec.title, kpis=kpis, statistics=statistics,
            findings=findings, trends=trends,
        )
