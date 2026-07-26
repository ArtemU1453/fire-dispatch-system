"""ExportService — the single export interface (stage §5, §11).

Renders an analytics dataset (KPIs, a statistics section, or trends) for a period
into CSV or XLSX, enforces RBAC and **logs every export** to the existing
``audit_logs`` trail (reusing the Administration audit recorder). PDF is a future
format that plugs into the same interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.audit import AdminAuditRecorder
from app.admin.utils.actor import Actor
from app.analytics.export import ExportFormat, TableData, media_type, render
from app.analytics.repositories import AnalyticsRepository
from app.analytics.services.kpi_service import KPIService
from app.analytics.services.trends_service import TrendsService
from app.analytics.statistics import StatisticsService
from app.analytics.utils.period import Period
from app.analytics.utils.rbac import AnalyticsAccess
from app.core.exceptions import ValidationError
from app.models.enums import AuditAction

DATASETS = (
    "kpi", "incident_types", "districts", "unit_load", "call_dynamics", "trends",
)


@dataclass(slots=True)
class ExportResult:
    filename: str
    media_type: str
    content: bytes
    rows: int


class ExportService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AnalyticsRepository(session)
        self._access = AnalyticsAccess(session)
        self._audit = AdminAuditRecorder(session)

    async def export(
        self,
        dataset: str,
        fmt: ExportFormat,
        period: Period,
        *,
        actor_id: UUID | None = None,
        actor_name: str | None = None,
    ) -> ExportResult:
        if dataset not in DATASETS:
            raise ValidationError(f"Unknown dataset: {dataset}")
        await self._access.require(actor_id, "analytics.export")

        table = await self._build_table(dataset, period)
        content = render(table, fmt)
        filename = (
            f"analytics_{dataset}_{period.kind.value}_"
            f"{datetime.now(tz=UTC):%Y%m%d%H%M%S}.{fmt.value}"
        )

        # Export is audited (no sensitive data — only metadata about the export).
        self._audit.record(
            AuditAction.CREATE, "analytics_export",
            changes={
                "dataset": dataset, "format": fmt.value,
                "period": period.kind.value, "rows": len(table.rows),
            },
            actor=Actor(user_id=actor_id, name=actor_name),
        )
        await self._session.flush()
        return ExportResult(
            filename=filename, media_type=media_type(fmt),
            content=content, rows=len(table.rows),
        )

    async def _build_table(self, dataset: str, period: Period) -> TableData:
        if dataset == "kpi":
            values = await KPIService(self._repo).compute(period)
            return TableData(
                title="KPI",
                columns=["Ключ", "Показатель", "Значение", "Ед."],
                rows=[[v.key, v.name, v.value, v.unit] for v in values],
            )
        if dataset == "trends":
            trends = await TrendsService(self._repo).compute(period)
            return TableData(
                title="Тенденции",
                columns=["Ключ", "Показатель", "Текущее", "Предыдущее",
                         "Изменение, %", "Направление"],
                rows=[
                    [t.key, t.name, t.current, t.previous, t.change_pct,
                     t.direction]
                    for t in trends
                ],
            )
        stats = await StatisticsService(self._repo).compute(period)
        section = {
            "incident_types": ("Типы происшествий", stats.by_incident_type),
            "districts": ("Районы", stats.by_district),
            "unit_load": ("Нагрузка подразделений", stats.unit_load),
            "call_dynamics": ("Динамика вызовов", stats.call_dynamics),
        }[dataset]
        title, rows = section
        return TableData(
            title=title, columns=["Категория", "Количество"],
            rows=[[d.label, d.count] for d in rows],
        )
