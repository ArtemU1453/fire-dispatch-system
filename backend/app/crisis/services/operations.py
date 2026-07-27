"""Operation & headquarters services (Stage 20 §2, §4)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.crisis.models.entities import (
    CommandAssignment,
    CrisisResponseLevel,
    EmergencyOperation,
    OperationalHeadquarters,
)
from app.crisis.models.enums import CommandRole, JournalKind, OperationStatus
from app.crisis.repositories.repositories import (
    CommandAssignmentRepository,
    HeadquartersRepository,
    OperationRepository,
    ResponseLevelRepository,
)
from app.crisis.services.access import (
    PERM_COMMAND,
    PERM_MANAGE,
    PERM_VIEW,
    CrisisAccess,
)
from app.crisis.services.journal import JournalService
from app.repositories.base import QuerySpec

_VALID_STATUS = {s.value for s in OperationStatus}


class OperationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._ops = OperationRepository(session)
        self._hq = HeadquartersRepository(session)
        self._cmd = CommandAssignmentRepository(session)
        self._levels = ResponseLevelRepository(session)
        self._journal = JournalService(session)
        self._access = CrisisAccess(session)

    # -------------------------------------------------------------- levels
    async def list_levels(self) -> list[CrisisResponseLevel]:
        return list(
            await self._levels.list(
                QuerySpec(filters={"is_active": True}, order_by=["rank"], limit=100)
            )
        )

    async def _resolve_level(self, code: str | None) -> UUID | None:
        if not code:
            return None
        row = (
            await self._session.execute(
                select(CrisisResponseLevel).where(CrisisResponseLevel.code == code)
            )
        ).scalar_one_or_none()
        if row is None:
            raise ValidationError(f"Unknown response level: {code}")
        return row.id

    # ---------------------------------------------------------- operations
    async def create(
        self,
        *,
        name: str,
        code: str,
        response_level_code: str | None = None,
        incident_ref: str | None = None,
        description: str | None = None,
        started_at: datetime | None = None,
        actor: str | None = None,
        user_id: UUID | None = None,
    ) -> EmergencyOperation:
        await self._access.require(user_id, PERM_MANAGE)
        existing = (
            await self._session.execute(
                select(EmergencyOperation).where(EmergencyOperation.code == code)
            )
        ).scalar_one_or_none()
        if existing is not None:
            raise ConflictError(f"Operation code already exists: {code}")
        level_id = await self._resolve_level(response_level_code)
        operation = await self._ops.add(
            EmergencyOperation(
                name=name,
                code=code,
                status=OperationStatus.PLANNED.value,
                response_level_id=level_id,
                incident_ref=incident_ref,
                description=description,
                started_at=started_at,
            )
        )
        # Every operation gets a headquarters (§4).
        await self._hq.add(
            OperationalHeadquarters(
                operation_id=operation.id, name=f"Штаб — {operation.name}"
            )
        )
        await self._journal.append(
            operation.id,
            kind=JournalKind.ACTION,
            message=f"Создана операция «{operation.name}» ({operation.code})",
            actor_ref=actor,
        )
        return operation

    async def list(
        self, *, status: str | None = None, user_id: UUID | None = None
    ) -> list[EmergencyOperation]:
        await self._access.require(user_id, PERM_VIEW)
        filters: dict[str, Any] = {}
        if status:
            filters["status"] = status
        return list(
            await self._ops.list(
                QuerySpec(filters=filters, order_by=["-created_at"], limit=200)
            )
        )

    async def get(
        self, operation_id: UUID, *, user_id: UUID | None = None
    ) -> EmergencyOperation:
        await self._access.require(user_id, PERM_VIEW)
        operation = await self._ops.get(operation_id)
        if operation is None:
            raise NotFoundError(f"Operation not found: {operation_id}")
        return operation

    async def update(
        self,
        operation_id: UUID,
        *,
        values: dict[str, Any],
        actor: str | None = None,
        user_id: UUID | None = None,
    ) -> EmergencyOperation:
        await self._access.require(user_id, PERM_MANAGE)
        operation = await self.get(operation_id, user_id=user_id)
        allowed: dict[str, Any] = {}
        if "name" in values and values["name"]:
            allowed["name"] = values["name"]
        if "description" in values:
            allowed["description"] = values["description"]
        if "status" in values and values["status"]:
            if values["status"] not in _VALID_STATUS:
                raise ValidationError(f"Invalid status: {values['status']}")
            allowed["status"] = values["status"]
            if values["status"] == OperationStatus.CLOSED.value:
                allowed["ended_at"] = datetime.now(tz=UTC)
        if "response_level_code" in values:
            allowed["response_level_id"] = await self._resolve_level(
                values["response_level_code"]
            )
        if "started_at" in values:
            allowed["started_at"] = values["started_at"]
        operation = await self._ops.update(operation, allowed)
        changed = ", ".join(sorted(allowed)) or "нет изменений"
        await self._journal.append(
            operation.id,
            kind=JournalKind.ACTION,
            message=f"Обновлена операция: {changed}",
            actor_ref=actor,
            payload={"changes": {k: str(v) for k, v in allowed.items()}},
        )
        return operation

    # ------------------------------------------------------- headquarters
    async def headquarters(
        self, operation_id: UUID, *, user_id: UUID | None = None
    ) -> OperationalHeadquarters:
        await self._access.require(user_id, PERM_VIEW)
        hq = (
            await self._session.execute(
                select(OperationalHeadquarters).where(
                    OperationalHeadquarters.operation_id == operation_id,
                    OperationalHeadquarters.is_deleted.is_(False),
                )
            )
        ).scalar_one_or_none()
        if hq is None:
            raise NotFoundError(f"Headquarters not found for operation {operation_id}")
        return hq

    async def assign_command(
        self,
        operation_id: UUID,
        *,
        role: str,
        user_ref: str,
        display_name: str | None = None,
        responsibilities: str | None = None,
        actor: str | None = None,
        user_id: UUID | None = None,
    ) -> CommandAssignment:
        await self._access.require(user_id, PERM_COMMAND)
        if role not in {r.value for r in CommandRole}:
            raise ValidationError(f"Invalid command role: {role}")
        hq = await self.headquarters(operation_id, user_id=user_id)
        assignment = await self._cmd.add(
            CommandAssignment(
                headquarters_id=hq.id,
                role=role,
                user_ref=user_ref,
                display_name=display_name,
                responsibilities=responsibilities,
            )
        )
        await self._journal.append(
            operation_id,
            kind=JournalKind.ASSIGNMENT,
            message=f"Назначен {role}: {display_name or user_ref}",
            actor_ref=actor,
        )
        return assignment

    async def command_members(
        self, operation_id: UUID, *, user_id: UUID | None = None
    ) -> list[CommandAssignment]:
        hq = await self.headquarters(operation_id, user_id=user_id)
        return list(
            await self._cmd.list(
                QuerySpec(
                    filters={"headquarters_id": hq.id},
                    order_by=["created_at"], limit=100,
                )
            )
        )

    async def record_decision(
        self,
        operation_id: UUID,
        *,
        decision: str,
        rationale: str | None = None,
        actor: str | None = None,
        user_id: UUID | None = None,
    ):
        await self._access.require(user_id, PERM_COMMAND)
        await self.get(operation_id, user_id=user_id)
        return await self._journal.append(
            operation_id,
            kind=JournalKind.DECISION,
            message=decision,
            rationale=rationale,
            actor_ref=actor,
        )
