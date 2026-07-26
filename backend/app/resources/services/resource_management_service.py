"""ResourceManagementService — real-time unit / vehicle / personnel state.

Keeps the current state of every unit, vehicle and crew, updates statuses,
manages crews and incident assignments, and records an append-only history.

**Dispatch integration without changing the Dispatch Engine:** a status change on
a vehicle / unit updates the underlying Stage-2 ``resources.availability_status``
that the Dispatch Engine already reads — so the engine always uses the current
data from this module, and no engine code is touched. The existing
``status_history`` table is also written, alongside this module's own history.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.catalog import AvailabilityStatus
from app.models.history import StatusHistory
from app.models.resource import Resource
from app.resources.models.entities import (
    Crew,
    CrewMember,
    ResourceAssignment,
    ResourceManagementHistory,
    Unit,
)
from app.resources.models.enums import AssignmentStatus, ResourceEventType
from app.resources.repositories import ResourceManagementRepository
from app.resources.tracking import Position, StoredPositionProvider


def _now() -> datetime:
    return datetime.now(tz=UTC)


class ResourceManagementService:
    """Manages the live state of units, vehicles, crews and personnel."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ResourceManagementRepository(session)
        self._positions = StoredPositionProvider(session)

    # ------------------------------------------------------------- reads
    async def list_units(self, **kwargs) -> Sequence[Unit]:
        return await self._repo.units(**kwargs)

    async def get_unit(self, unit_id: UUID) -> Unit:
        unit = await self._repo.unit_full(unit_id)
        if unit is None:
            raise NotFoundError("Unit not found")
        return unit

    async def list_vehicles(self, **kwargs) -> Sequence[Resource]:
        return await self._repo.vehicles(**kwargs)

    async def get_vehicle(self, resource_id: UUID) -> Resource:
        vehicle = await self._repo.vehicle(resource_id)
        if vehicle is None:
            raise NotFoundError("Vehicle not found")
        return vehicle

    async def vehicle_states(self, resource_ids):
        return await self._repo.vehicle_states(resource_ids)

    async def list_crews(self, **kwargs) -> Sequence[Crew]:
        return await self._repo.crews(**kwargs)

    async def list_personnel(self, **kwargs) -> Sequence[Resource]:
        return await self._repo.personnel(**kwargs)

    async def get_personnel(self, resource_id: UUID) -> Resource:
        person = await self._repo.personnel_one(resource_id)
        if person is None:
            raise NotFoundError("Personnel not found")
        return person

    async def qualifications(self, resource_ids):
        return await self._repo.qualifications(resource_ids)

    async def status_overview(self):
        return await self._repo.status_overview()

    async def history(self, **kwargs):
        return await self._repo.history(**kwargs)

    async def get_location(self, resource_id: UUID) -> Position | None:
        return await self._positions.get_position(resource_id)

    async def check_availability(self, resource_id: UUID) -> bool:
        resource = await self._session.get(Resource, resource_id)
        if resource is None or resource.availability_status_id is None:
            return False
        status = await self._session.get(
            AvailabilityStatus, resource.availability_status_id
        )
        return bool(status and status.is_available_for_dispatch)

    # ---------------------------------------------------------- statuses
    async def _resolve_status(self, code: str) -> AvailabilityStatus:
        status = await self._repo.status_by_code(code)
        if status is None:
            raise ValidationError(f"Unknown status code: {code!r}")
        return status

    async def _apply_resource_status(
        self,
        resource_id: UUID,
        status: AvailabilityStatus,
        *,
        reason: str | None,
    ) -> tuple[UUID | None, UUID]:
        """Set the resource's status (Dispatch-visible) + write status_history."""
        resource = await self._session.get(Resource, resource_id)
        if resource is None:
            raise NotFoundError("Resource not found")
        old_status_id = resource.availability_status_id
        resource.availability_status_id = status.id
        self._session.add(
            StatusHistory(
                resource_id=resource_id,
                from_status_id=old_status_id,
                to_status_id=status.id,
                changed_at=_now(),
                reason=reason,
            )
        )
        return old_status_id, status.id

    def _record(
        self,
        event_type: ResourceEventType,
        *,
        resource_id: UUID | None = None,
        unit_id: UUID | None = None,
        crew_id: UUID | None = None,
        from_value: str | None = None,
        to_value: str | None = None,
        actor_name: str | None = None,
        incident_id: UUID | None = None,
        meta: dict[str, Any] | None = None,
    ) -> None:
        self._session.add(
            ResourceManagementHistory(
                resource_id=resource_id,
                unit_id=unit_id,
                crew_id=crew_id,
                event_type=event_type,
                from_value=from_value,
                to_value=to_value,
                changed_by_name=actor_name,
                incident_id=incident_id,
                meta=meta,
            )
        )

    async def update_unit_status(
        self,
        unit_id: UUID,
        status_code: str,
        *,
        actor_name: str | None = None,
        reason: str | None = None,
        incident_id: UUID | None = None,
    ) -> Unit:
        unit = await self.get_unit(unit_id)
        status = await self._resolve_status(status_code)
        old = unit.availability_status
        old_code = old.code if old else None
        # Assign the relationship (not just the FK) so the already-loaded M2O is
        # refreshed and the re-read below reflects the new status.
        unit.availability_status = status
        # Propagate to the unit's vehicle resource so the Dispatch Engine sees it.
        if unit.vehicle_resource_id is not None:
            await self._apply_resource_status(
                unit.vehicle_resource_id, status, reason=reason
            )
        self._record(
            ResourceEventType.UNIT_STATUS_CHANGED,
            unit_id=unit_id,
            resource_id=unit.vehicle_resource_id,
            from_value=old_code,
            to_value=status.code,
            actor_name=actor_name,
            incident_id=incident_id,
        )
        await self._session.flush()
        return await self.get_unit(unit_id)

    async def update_resource_status(
        self,
        resource_id: UUID,
        status_code: str,
        *,
        event: ResourceEventType,
        actor_name: str | None = None,
        reason: str | None = None,
        incident_id: UUID | None = None,
    ) -> UUID:
        status = await self._resolve_status(status_code)
        old_id, _ = await self._apply_resource_status(
            resource_id, status, reason=reason
        )
        old = (
            await self._session.get(AvailabilityStatus, old_id)
            if old_id
            else None
        )
        self._record(
            event,
            resource_id=resource_id,
            from_value=old.code if old else None,
            to_value=status.code,
            actor_name=actor_name,
            incident_id=incident_id,
        )
        await self._session.flush()
        return resource_id  # caller re-reads via repository

    async def bulk_update_status(
        self,
        resource_ids: Sequence[UUID],
        status_code: str,
        *,
        actor_name: str | None = None,
        reason: str | None = None,
    ) -> int:
        """Efficient mass status update (single UPDATE + batched history)."""
        if not resource_ids:
            return 0
        status = await self._resolve_status(status_code)
        result = await self._session.execute(
            update(Resource)
            .where(Resource.id.in_(list(resource_ids)))
            .values(availability_status_id=status.id)
        )
        now = _now()
        for rid in resource_ids:
            self._session.add(
                StatusHistory(
                    resource_id=rid, to_status_id=status.id,
                    changed_at=now, reason=reason,
                )
            )
            self._record(
                ResourceEventType.VEHICLE_STATUS_CHANGED,
                resource_id=rid, to_value=status.code, actor_name=actor_name,
            )
        await self._session.flush()
        return result.rowcount or 0

    # ------------------------------------------------------------- crews
    async def assign_crew(
        self, unit_id: UUID, crew_id: UUID, *, actor_name: str | None = None
    ) -> Unit:
        await self.get_unit(unit_id)  # validates the unit exists
        crew = await self._session.get(Crew, crew_id)
        if crew is None:
            raise NotFoundError("Crew not found")
        crew.unit_id = unit_id
        crew.is_on_duty = True
        self._record(
            ResourceEventType.CREW_CHANGED,
            unit_id=unit_id, crew_id=crew_id, to_value=crew.code,
            actor_name=actor_name,
        )
        await self._session.flush()
        return await self.get_unit(unit_id)

    async def change_crew_composition(
        self,
        crew_id: UUID,
        *,
        add: Sequence[UUID] = (),
        remove: Sequence[UUID] = (),
        actor_name: str | None = None,
    ) -> Crew:
        crew = await self._repo.crew(crew_id)
        if crew is None:
            raise NotFoundError("Crew not found")
        existing = {m.personnel_resource_id for m in crew.members if not m.is_deleted}
        for resource_id in add:
            if resource_id not in existing:
                crew.members.append(
                    CrewMember(personnel_resource_id=resource_id)
                )
                existing.add(resource_id)
        removal = set(remove)
        for member in crew.members:
            if member.personnel_resource_id in removal:
                member.left_at = _now()
                member.is_deleted = True
        self._record(
            ResourceEventType.CREW_MEMBER_CHANGED,
            crew_id=crew_id,
            actor_name=actor_name,
            meta={
                "added": [str(i) for i in add],
                "removed": [str(i) for i in remove],
            },
        )
        await self._session.flush()
        return await self._require_crew(crew_id)

    # -------------------------------------------------------- assignments
    async def assign_to_incident(
        self,
        unit_id: UUID,
        incident_id: UUID,
        *,
        role: str = "primary",
        actor_name: str | None = None,
    ) -> Unit:
        unit = await self.get_unit(unit_id)
        unit.assignments.append(
            ResourceAssignment(
                incident_id=incident_id, role=role, status=AssignmentStatus.ACTIVE
            )
        )
        self._record(
            ResourceEventType.ASSIGNED,
            unit_id=unit_id, resource_id=unit.vehicle_resource_id,
            incident_id=incident_id, to_value=role, actor_name=actor_name,
        )
        await self._session.flush()
        return await self.get_unit(unit_id)

    async def return_from_incident(
        self, unit_id: UUID, *, actor_name: str | None = None
    ) -> Unit:
        unit = await self.get_unit(unit_id)
        released = 0
        for assignment in unit.assignments:
            is_active = assignment.status is AssignmentStatus.ACTIVE
            if is_active and not assignment.is_deleted:
                assignment.status = AssignmentStatus.RELEASED
                assignment.released_at = _now()
                released += 1
        self._record(
            ResourceEventType.RETURNED,
            unit_id=unit_id, resource_id=unit.vehicle_resource_id,
            to_value=str(released), actor_name=actor_name,
        )
        await self._session.flush()
        return await self.get_unit(unit_id)

    async def _require_crew(self, crew_id: UUID) -> Crew:
        crew = await self._repo.crew(crew_id)
        if crew is None:  # pragma: no cover
            raise NotFoundError("Crew not found")
        return crew
