"""Situation board & reports services (Stage 20 §2, §9).

The situation board aggregates the live operational picture — active sectors,
forces & means (resource groups), zones (for the GIS map), recent critical
journal events and the latest situation report. It reads existing crisis data
only; geographic rendering uses the existing GIS API on the client.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crisis.models.entities import OperationalOrder, SituationReport
from app.crisis.models.enums import JournalKind
from app.crisis.repositories.repositories import (
    OperationalOrderRepository,
    SituationReportRepository,
)
from app.crisis.services.access import PERM_MANAGE, PERM_VIEW, CrisisAccess
from app.crisis.services.journal import JournalService
from app.crisis.services.resources import ResourceGroupService
from app.crisis.services.sectors import SectorService
from app.repositories.base import QuerySpec


class ReportService:
    def __init__(self, session: AsyncSession) -> None:
        self._reports = SituationReportRepository(session)
        self._orders = OperationalOrderRepository(session)
        self._access = CrisisAccess(session)

    async def add_report(
        self,
        operation_id: UUID,
        *,
        summary: str,
        author_ref: str | None = None,
        data: dict[str, Any] | None = None,
        user_id: UUID | None = None,
    ) -> SituationReport:
        await self._access.require(user_id, PERM_MANAGE)
        return await self._reports.add(
            SituationReport(
                operation_id=operation_id,
                summary=summary,
                author_ref=author_ref,
                data=data,
            )
        )

    async def list_reports(
        self, operation_id: UUID, *, user_id: UUID | None = None
    ) -> list[SituationReport]:
        await self._access.require(user_id, PERM_VIEW)
        return list(
            await self._reports.list(
                QuerySpec(
                    filters={"operation_id": operation_id},
                    order_by=["-created_at"], limit=100,
                )
            )
        )

    async def add_order(
        self,
        operation_id: UUID,
        *,
        number: str,
        text: str,
        issued_by_ref: str | None = None,
        user_id: UUID | None = None,
    ) -> OperationalOrder:
        await self._access.require(user_id, PERM_MANAGE)
        return await self._orders.add(
            OperationalOrder(
                operation_id=operation_id,
                number=number,
                text=text,
                issued_by_ref=issued_by_ref,
            )
        )


class SituationBoardService:
    def __init__(self, session: AsyncSession) -> None:
        self._sectors = SectorService(session)
        self._groups = ResourceGroupService(session)
        self._reports = ReportService(session)
        self._journal = JournalService(session)
        self._access = CrisisAccess(session)

    async def board(self, operation_id: UUID, *, user_id: UUID | None = None) -> dict:
        await self._access.require(user_id, PERM_VIEW)
        sectors = await self._sectors.list_sectors(operation_id, user_id=user_id)
        zones = await self._sectors.list_zones(operation_id, user_id=user_id)
        groups = await self._groups.list_groups(operation_id, user_id=user_id)
        reports = await self._reports.list_reports(operation_id, user_id=user_id)
        # Critical events = decisions + situation changes, most recent first.
        events = await self._journal.timeline(operation_id, limit=50)
        critical = [
            e
            for e in events
            if e.kind in (JournalKind.DECISION.value, JournalKind.SITUATION.value)
        ]
        return {
            "operation_id": operation_id,
            "sectors": sectors,
            "zones": zones,
            "resource_groups": groups,
            "critical_events": list(reversed(critical))[:20],
            "latest_report": reports[0] if reports else None,
        }
