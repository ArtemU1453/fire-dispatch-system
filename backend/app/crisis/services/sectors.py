"""Operational sector & zone services (Stage 20 §5, §9)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.crisis.models.entities import OperationalSector, OperationalZone
from app.crisis.models.enums import JournalKind, SectorStatus, ZoneKind
from app.crisis.repositories.repositories import SectorRepository, ZoneRepository
from app.crisis.services.access import PERM_MANAGE, PERM_VIEW, CrisisAccess
from app.crisis.services.journal import JournalService
from app.repositories.base import QuerySpec

_VALID_SECTOR_STATUS = {s.value for s in SectorStatus}
_VALID_ZONE_KIND = {z.value for z in ZoneKind}


class SectorService:
    def __init__(self, session: AsyncSession) -> None:
        self._sectors = SectorRepository(session)
        self._zones = ZoneRepository(session)
        self._journal = JournalService(session)
        self._access = CrisisAccess(session)

    async def create_sector(
        self,
        operation_id: UUID,
        *,
        name: str,
        leader_ref: str | None = None,
        center_lat: float | None = None,
        center_lon: float | None = None,
        actor: str | None = None,
        user_id: UUID | None = None,
    ) -> OperationalSector:
        await self._access.require(user_id, PERM_MANAGE)
        sector = await self._sectors.add(
            OperationalSector(
                operation_id=operation_id,
                name=name,
                leader_ref=leader_ref,
                status=SectorStatus.FORMING.value,
                center_lat=center_lat,
                center_lon=center_lon,
            )
        )
        await self._journal.append(
            operation_id,
            kind=JournalKind.ACTION,
            message=f"Создан оперативный участок «{name}»",
            actor_ref=actor,
        )
        return sector

    async def list_sectors(
        self, operation_id: UUID, *, user_id: UUID | None = None
    ) -> list[OperationalSector]:
        await self._access.require(user_id, PERM_VIEW)
        return list(
            await self._sectors.list(
                QuerySpec(
                    filters={"operation_id": operation_id},
                    order_by=["position", "created_at"], limit=200,
                )
            )
        )

    async def get_sector(self, sector_id: UUID) -> OperationalSector:
        sector = await self._sectors.get(sector_id)
        if sector is None:
            raise NotFoundError(f"Sector not found: {sector_id}")
        return sector

    async def update_sector(
        self,
        sector_id: UUID,
        *,
        values: dict[str, Any],
        actor: str | None = None,
        user_id: UUID | None = None,
    ) -> OperationalSector:
        await self._access.require(user_id, PERM_MANAGE)
        sector = await self.get_sector(sector_id)
        allowed: dict[str, Any] = {}
        for key in ("name", "leader_ref", "situation", "center_lat", "center_lon"):
            if key in values:
                allowed[key] = values[key]
        if "status" in values and values["status"]:
            if values["status"] not in _VALID_SECTOR_STATUS:
                raise ValidationError(f"Invalid sector status: {values['status']}")
            allowed["status"] = values["status"]
        sector = await self._sectors.update(sector, allowed)
        await self._journal.append(
            sector.operation_id,
            kind=JournalKind.SITUATION,
            message=f"Изменён участок «{sector.name}»",
            actor_ref=actor,
        )
        return sector

    # ------------------------------------------------------------- zones
    async def create_zone(
        self,
        operation_id: UUID,
        *,
        label: str,
        kind: str = ZoneKind.HOT.value,
        sector_id: UUID | None = None,
        center_lat: float | None = None,
        center_lon: float | None = None,
        radius_m: float | None = None,
        user_id: UUID | None = None,
    ) -> OperationalZone:
        await self._access.require(user_id, PERM_MANAGE)
        if kind not in _VALID_ZONE_KIND:
            raise ValidationError(f"Invalid zone kind: {kind}")
        return await self._zones.add(
            OperationalZone(
                operation_id=operation_id,
                sector_id=sector_id,
                label=label,
                kind=kind,
                center_lat=center_lat,
                center_lon=center_lon,
                radius_m=radius_m,
            )
        )

    async def list_zones(
        self, operation_id: UUID, *, user_id: UUID | None = None
    ) -> list[OperationalZone]:
        await self._access.require(user_id, PERM_VIEW)
        return list(
            await self._zones.list(
                QuerySpec(
                    filters={"operation_id": operation_id},
                    order_by=["created_at"], limit=200,
                )
            )
        )
