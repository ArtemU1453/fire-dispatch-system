"""Repositories for resource management (eager reads, no N+1).

Reads span the new operational tables (units, crews, assignments) and the
existing Stage-2 resource model (resources / vehicles / personnel / availability
statuses), which are referenced but never modified.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.catalog import AvailabilityStatus
from app.models.enums import ResourceCategory
from app.models.resource import Resource
from app.resources.models.entities import (
    Crew,
    CrewMember,
    PersonnelQualification,
    ResourceManagementHistory,
    Unit,
    VehicleState,
)


def _unit_options() -> list:
    return [
        selectinload(Unit.station),
        selectinload(Unit.organization),
        selectinload(Unit.vehicle),
        selectinload(Unit.availability_status),
        selectinload(Unit.crews).selectinload(Crew.members),
        selectinload(Unit.assignments),
    ]


class ResourceManagementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # -------------------------------------------------------------- units
    async def unit_full(self, unit_id: UUID) -> Unit | None:
        stmt = (
            select(Unit)
            .where(Unit.id == unit_id, Unit.is_deleted.is_(False))
            .options(*_unit_options())
        )
        return (await self._session.execute(stmt)).scalars().first()

    async def units(
        self,
        *,
        organization_id: UUID | None = None,
        active_only: bool = False,
        limit: int = 200,
        offset: int = 0,
    ) -> Sequence[Unit]:
        stmt = select(Unit).where(Unit.is_deleted.is_(False))
        if organization_id is not None:
            stmt = stmt.where(Unit.organization_id == organization_id)
        if active_only:
            stmt = stmt.where(Unit.is_active.is_(True))
        stmt = (
            stmt.order_by(Unit.code).limit(limit).offset(offset).options(*_unit_options())
        )
        return (await self._session.execute(stmt)).scalars().all()

    # ------------------------------------------------------ vehicles/personnel
    def _by_category(self, category: ResourceCategory):
        from app.models.assets import Personnel, Vehicle

        return (
            select(Resource)
            .join(Resource.resource_type)
            .where(Resource.is_deleted.is_(False))
            .where(Resource.resource_type.has(category=category))
            .options(
                selectinload(Resource.resource_type),
                selectinload(Resource.availability_status),
                selectinload(Resource.organization),
                selectinload(Resource.vehicle).selectinload(Vehicle.vehicle_type),
                selectinload(Resource.personnel).selectinload(Personnel.role),
            )
        )

    async def vehicles(
        self, *, limit: int = 200, offset: int = 0
    ) -> Sequence[Resource]:
        stmt = self._by_category(ResourceCategory.VEHICLE).order_by(
            Resource.code
        ).limit(limit).offset(offset)
        return (await self._session.execute(stmt)).scalars().all()

    async def vehicle(self, resource_id: UUID) -> Resource | None:
        stmt = self._by_category(ResourceCategory.VEHICLE).where(
            Resource.id == resource_id
        )
        return (await self._session.execute(stmt)).scalars().first()

    async def personnel(
        self, *, limit: int = 200, offset: int = 0
    ) -> Sequence[Resource]:
        stmt = self._by_category(ResourceCategory.PERSONNEL).order_by(
            Resource.code
        ).limit(limit).offset(offset)
        return (await self._session.execute(stmt)).scalars().all()

    async def personnel_one(self, resource_id: UUID) -> Resource | None:
        stmt = self._by_category(ResourceCategory.PERSONNEL).where(
            Resource.id == resource_id
        )
        return (await self._session.execute(stmt)).scalars().first()

    async def vehicle_states(
        self, resource_ids: Sequence[UUID]
    ) -> dict[UUID, VehicleState]:
        if not resource_ids:
            return {}
        rows = await self._session.execute(
            select(VehicleState).where(
                VehicleState.vehicle_resource_id.in_(list(resource_ids)),
                VehicleState.is_deleted.is_(False),
            )
        )
        return {v.vehicle_resource_id: v for v in rows.scalars().all()}

    async def qualifications(
        self, resource_ids: Sequence[UUID]
    ) -> dict[UUID, list[PersonnelQualification]]:
        if not resource_ids:
            return {}
        rows = await self._session.execute(
            select(PersonnelQualification).where(
                PersonnelQualification.personnel_resource_id.in_(list(resource_ids)),
                PersonnelQualification.is_deleted.is_(False),
            )
        )
        out: dict[UUID, list[PersonnelQualification]] = {}
        for q in rows.scalars().all():
            out.setdefault(q.personnel_resource_id, []).append(q)
        return out

    # ------------------------------------------------------------- crews
    async def crews(
        self, *, on_duty: bool | None = None, limit: int = 200, offset: int = 0
    ) -> Sequence[Crew]:
        stmt = select(Crew).where(Crew.is_deleted.is_(False))
        if on_duty is not None:
            stmt = stmt.where(Crew.is_on_duty.is_(on_duty))
        stmt = (
            stmt.order_by(Crew.code)
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(Crew.shift),
                selectinload(Crew.members).selectinload(CrewMember.personnel),
            )
        )
        return (await self._session.execute(stmt)).scalars().all()

    async def crew(self, crew_id: UUID) -> Crew | None:
        stmt = (
            select(Crew)
            .where(Crew.id == crew_id, Crew.is_deleted.is_(False))
            .options(
                selectinload(Crew.shift),
                selectinload(Crew.members).selectinload(CrewMember.personnel),
            )
        )
        return (await self._session.execute(stmt)).scalars().first()

    # ------------------------------------------------------------ statuses
    async def status_by_code(self, code: str) -> AvailabilityStatus | None:
        stmt = select(AvailabilityStatus).where(
            AvailabilityStatus.code == code,
            AvailabilityStatus.is_deleted.is_(False),
        )
        return (await self._session.execute(stmt)).scalars().first()

    async def status_overview(self) -> list[tuple[AvailabilityStatus, int]]:
        stmt = (
            select(AvailabilityStatus, func.count(Resource.id))
            .outerjoin(
                Resource,
                (Resource.availability_status_id == AvailabilityStatus.id)
                & (Resource.is_deleted.is_(False)),
            )
            .where(AvailabilityStatus.is_deleted.is_(False))
            .group_by(AvailabilityStatus.id)
            .order_by(AvailabilityStatus.sort_order)
        )
        rows = (await self._session.execute(stmt)).all()
        return [(status, count) for status, count in rows]

    # ------------------------------------------------------------- history
    async def history(
        self,
        *,
        resource_id: UUID | None = None,
        unit_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ResourceManagementHistory]:
        stmt = select(ResourceManagementHistory)
        if resource_id is not None:
            stmt = stmt.where(ResourceManagementHistory.resource_id == resource_id)
        if unit_id is not None:
            stmt = stmt.where(ResourceManagementHistory.unit_id == unit_id)
        stmt = (
            stmt.order_by(ResourceManagementHistory.occurred_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return (await self._session.execute(stmt)).scalars().all()
