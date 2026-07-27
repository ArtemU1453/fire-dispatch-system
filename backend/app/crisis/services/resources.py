"""Resource-group services: grouping, membership, relocation (Stage 20 §6)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.crisis.models.entities import (
    ResourceGroup,
    ResourceGroupMember,
    ResourceMove,
)
from app.crisis.models.enums import JournalKind, ResourceMemberKind
from app.crisis.repositories.repositories import (
    ResourceGroupMemberRepository,
    ResourceGroupRepository,
    ResourceMoveRepository,
)
from app.crisis.services.access import PERM_RESOURCE, PERM_VIEW, CrisisAccess
from app.crisis.services.journal import JournalService
from app.repositories.base import QuerySpec

_VALID_MEMBER_KIND = {k.value for k in ResourceMemberKind}


class ResourceGroupService:
    def __init__(self, session: AsyncSession) -> None:
        self._groups = ResourceGroupRepository(session)
        self._members = ResourceGroupMemberRepository(session)
        self._moves = ResourceMoveRepository(session)
        self._journal = JournalService(session)
        self._access = CrisisAccess(session)

    async def create_group(
        self,
        operation_id: UUID,
        *,
        name: str,
        purpose: str | None = None,
        sector_id: UUID | None = None,
        actor: str | None = None,
        user_id: UUID | None = None,
    ) -> ResourceGroup:
        await self._access.require(user_id, PERM_RESOURCE)
        group = await self._groups.add(
            ResourceGroup(
                operation_id=operation_id,
                name=name,
                purpose=purpose,
                sector_id=sector_id,
            )
        )
        await self._journal.append(
            operation_id,
            kind=JournalKind.ASSIGNMENT,
            message=f"Создана группировка сил «{name}»",
            actor_ref=actor,
        )
        return group

    async def get_group(self, group_id: UUID) -> ResourceGroup:
        group = await self._groups.get(group_id)
        if group is None:
            raise NotFoundError(f"Resource group not found: {group_id}")
        return group

    async def list_groups(
        self, operation_id: UUID, *, user_id: UUID | None = None
    ) -> list[ResourceGroup]:
        await self._access.require(user_id, PERM_VIEW)
        return list(
            await self._groups.list(
                QuerySpec(
                    filters={"operation_id": operation_id},
                    order_by=["created_at"], limit=200,
                )
            )
        )

    async def add_member(
        self,
        group_id: UUID,
        *,
        kind: str,
        ref: str,
        label: str | None = None,
        actor: str | None = None,
        user_id: UUID | None = None,
    ) -> ResourceGroupMember:
        await self._access.require(user_id, PERM_RESOURCE)
        if kind not in _VALID_MEMBER_KIND:
            raise ValidationError(f"Invalid member kind: {kind}")
        group = await self.get_group(group_id)
        member = await self._members.add(
            ResourceGroupMember(group_id=group.id, kind=kind, ref=ref, label=label)
        )
        await self._journal.append(
            group.operation_id,
            kind=JournalKind.ASSIGNMENT,
            message=f"В группу «{group.name}» добавлен ресурс {label or ref}",
            actor_ref=actor,
        )
        return member

    async def members(self, group_id: UUID) -> list[ResourceGroupMember]:
        return list(
            await self._members.list(
                QuerySpec(
                    filters={"group_id": group_id}, order_by=["created_at"], limit=500
                )
            )
        )

    async def relocate(
        self,
        group_id: UUID,
        *,
        to_sector_id: UUID | None,
        note: str | None = None,
        actor: str | None = None,
        user_id: UUID | None = None,
    ) -> ResourceMove:
        """Move a group to another sector, recording the change history (§6)."""
        await self._access.require(user_id, PERM_RESOURCE)
        group = await self.get_group(group_id)
        from_sector_id = group.sector_id
        move = await self._moves.add(
            ResourceMove(
                group_id=group.id,
                from_sector_id=from_sector_id,
                to_sector_id=to_sector_id,
                note=note,
            )
        )
        await self._groups.update(group, {"sector_id": to_sector_id})
        await self._journal.append(
            group.operation_id,
            kind=JournalKind.ASSIGNMENT,
            message=f"Передислокация группы «{group.name}»",
            actor_ref=actor,
            payload={
                "from_sector": str(from_sector_id) if from_sector_id else None,
                "to_sector": str(to_sector_id) if to_sector_id else None,
            },
        )
        return move

    async def move_history(self, group_id: UUID) -> list[ResourceMove]:
        return list(
            await self._moves.list(
                QuerySpec(
                    filters={"group_id": group_id},
                    order_by=["created_at"], limit=200,
                )
            )
        )
