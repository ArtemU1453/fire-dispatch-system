"""Operational plan services: stages & tasks (Stage 20 §7)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.crisis.models.entities import OperationalTask, PlanStage
from app.crisis.models.enums import JournalKind, StageStatus, TaskStatus
from app.crisis.repositories.repositories import PlanStageRepository, TaskRepository
from app.crisis.services.access import PERM_MANAGE, PERM_VIEW, CrisisAccess
from app.crisis.services.journal import JournalService
from app.repositories.base import QuerySpec

_VALID_TASK_STATUS = {s.value for s in TaskStatus}
_VALID_STAGE_STATUS = {s.value for s in StageStatus}


class PlanService:
    def __init__(self, session: AsyncSession) -> None:
        self._stages = PlanStageRepository(session)
        self._tasks = TaskRepository(session)
        self._journal = JournalService(session)
        self._access = CrisisAccess(session)

    # ------------------------------------------------------------- stages
    async def add_stage(
        self,
        operation_id: UUID,
        *,
        name: str,
        position: int = 0,
        user_id: UUID | None = None,
    ) -> PlanStage:
        await self._access.require(user_id, PERM_MANAGE)
        return await self._stages.add(
            PlanStage(
                operation_id=operation_id,
                name=name,
                position=position,
                status=StageStatus.PLANNED.value,
            )
        )

    async def list_stages(
        self, operation_id: UUID, *, user_id: UUID | None = None
    ) -> list[PlanStage]:
        await self._access.require(user_id, PERM_VIEW)
        return list(
            await self._stages.list(
                QuerySpec(
                    filters={"operation_id": operation_id},
                    order_by=["position", "created_at"], limit=200,
                )
            )
        )

    async def set_stage_status(
        self, stage_id: UUID, status: str, *, user_id: UUID | None = None
    ) -> PlanStage:
        await self._access.require(user_id, PERM_MANAGE)
        if status not in _VALID_STAGE_STATUS:
            raise ValidationError(f"Invalid stage status: {status}")
        stage = await self._stages.get(stage_id)
        if stage is None:
            raise NotFoundError(f"Stage not found: {stage_id}")
        return await self._stages.update(stage, {"status": status})

    # -------------------------------------------------------------- tasks
    async def add_task(
        self,
        operation_id: UUID,
        *,
        title: str,
        description: str | None = None,
        stage_id: UUID | None = None,
        sector_id: UUID | None = None,
        assignee_ref: str | None = None,
        due_at: datetime | None = None,
        actor: str | None = None,
        user_id: UUID | None = None,
    ) -> OperationalTask:
        await self._access.require(user_id, PERM_MANAGE)
        task = await self._tasks.add(
            OperationalTask(
                operation_id=operation_id,
                stage_id=stage_id,
                sector_id=sector_id,
                title=title,
                description=description,
                assignee_ref=assignee_ref,
                due_at=due_at,
                status=TaskStatus.PENDING.value,
            )
        )
        await self._journal.append(
            operation_id,
            kind=JournalKind.ACTION,
            message=f"Поставлена задача: {title}",
            actor_ref=actor,
        )
        return task

    async def list_tasks(
        self,
        operation_id: UUID,
        *,
        sector_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> list[OperationalTask]:
        await self._access.require(user_id, PERM_VIEW)
        filters: dict[str, Any] = {"operation_id": operation_id}
        if sector_id is not None:
            filters["sector_id"] = sector_id
        return list(
            await self._tasks.list(
                QuerySpec(
                    filters=filters, order_by=["position", "created_at"], limit=500
                )
            )
        )

    async def set_task_status(
        self,
        task_id: UUID,
        status: str,
        *,
        actor: str | None = None,
        user_id: UUID | None = None,
    ) -> OperationalTask:
        await self._access.require(user_id, PERM_MANAGE)
        if status not in _VALID_TASK_STATUS:
            raise ValidationError(f"Invalid task status: {status}")
        task = await self._tasks.get(task_id)
        if task is None:
            raise NotFoundError(f"Task not found: {task_id}")
        task = await self._tasks.update(task, {"status": status})
        await self._journal.append(
            task.operation_id,
            kind=JournalKind.ACTION,
            message=f"Задача «{task.title}» → {status}",
            actor_ref=actor,
        )
        return task
