"""Directory (catalog) management (stage §5).

A single generic mechanism to maintain the system's catalogs — incident types,
categories, vehicle / unit / resource types, capabilities, statuses, priorities,
administrative territories, organizations — **as data, without code changes**.
Each catalog is a ``CatalogEntity`` table exposing ``code`` / ``name`` /
``description`` plus a few catalog-specific columns (exposed as ``extra``).

Only registered catalogs are editable; every change is audited.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.audit import AdminAuditRecorder, diff
from app.admin.models.entities import AccountStatus, IntegrationProvider
from app.admin.schemas.admin import DirectoryItemCreate, DirectoryItemUpdate
from app.admin.utils.actor import Actor
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.catalog import (
    AvailabilityStatus,
    Capability,
    EquipmentType,
    IncidentType,
    PersonnelRole,
    ResourceType,
    VehicleType,
)
from app.models.enums import AuditAction
from app.models.organization import Organization

# Registered, editable catalogs: name → (model, human label).
DIRECTORIES: dict[str, tuple[type, str]] = {
    "incident_types": (IncidentType, "Типы происшествий"),
    "resource_types": (ResourceType, "Типы ресурсов"),
    "vehicle_types": (VehicleType, "Типы техники"),
    "personnel_roles": (PersonnelRole, "Роли персонала"),
    "equipment_types": (EquipmentType, "Типы оборудования"),
    "capabilities": (Capability, "Возможности (Capability)"),
    "availability_statuses": (AvailabilityStatus, "Статусы доступности"),
    "organizations": (Organization, "Организации"),
    "account_statuses": (AccountStatus, "Статусы учётных записей"),
    "integration_providers": (IntegrationProvider, "Провайдеры интеграций"),
}

_BASE_COLUMNS = {
    "id", "created_at", "updated_at", "is_deleted", "code", "name", "description",
}


def editable_columns(model: type) -> list[str]:
    """Catalog-specific columns (beyond code / name / description)."""
    return [c.key for c in model.__table__.columns if c.key not in _BASE_COLUMNS]


def item_extra(item, model: type) -> dict[str, Any]:
    """The catalog-specific column values as JSON-safe primitives."""
    extra: dict[str, Any] = {}
    for key in editable_columns(model):
        value = getattr(item, key)
        if hasattr(value, "value"):  # enum
            value = value.value
        elif isinstance(value, UUID):
            value = str(value)
        extra[key] = value
    return extra


class DirectoryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AdminAuditRecorder(session)

    def resolve(self, name: str) -> type:
        entry = DIRECTORIES.get(name)
        if entry is None:
            raise NotFoundError(f"Unknown directory: {name}")
        return entry[0]

    def directories(self) -> list[tuple[str, str, list[str]]]:
        return [
            (name, label, editable_columns(model))
            for name, (model, label) in DIRECTORIES.items()
        ]

    async def list_items(
        self, name: str, *, include_deleted: bool = False
    ) -> Sequence:
        model = self.resolve(name)
        stmt = select(model)
        if not include_deleted:
            stmt = stmt.where(model.is_deleted.is_(False))
        stmt = stmt.order_by(model.code)
        return (await self._session.execute(stmt)).scalars().all()

    async def create_item(self, name: str, data: DirectoryItemCreate):
        model = self.resolve(name)
        if await self._by_code(model, data.code) is not None:
            raise ConflictError(f"Code already exists: {data.code}")
        actor = Actor(name=data.actor_name)
        item = model(code=data.code, name=data.name, description=data.description)
        self._apply_extra(model, item, data.extra)
        self._session.add(item)
        await self._session.flush()
        self._audit.record(
            AuditAction.CREATE, f"directory:{name}", entity_id=item.id,
            changes={"code": data.code}, actor=actor,
        )
        await self._session.flush()
        return item

    async def update_item(
        self, name: str, item_id: UUID, data: DirectoryItemUpdate
    ):
        model = self.resolve(name)
        item = await self._session.get(model, item_id)
        if item is None or item.is_deleted:
            raise NotFoundError("Directory item not found")
        actor = Actor(name=data.actor_name)
        before = {"name": item.name, "description": item.description}
        before_extra = item_extra(item, model)
        if data.name is not None:
            item.name = data.name
        if data.description is not None:
            item.description = data.description
        self._apply_extra(model, item, data.extra)
        after = {"name": item.name, "description": item.description}
        changes = diff(before, after)
        changes.update(diff(before_extra, item_extra(item, model)))
        if changes:
            self._audit.record(
                AuditAction.UPDATE, f"directory:{name}", entity_id=item.id,
                changes=changes, reason=data.reason, actor=actor,
            )
        await self._session.flush()
        return item

    # ------------------------------------------------------------ helpers
    @staticmethod
    def _apply_extra(model: type, item, extra: dict[str, Any]) -> None:
        allowed = set(editable_columns(model))
        for key, value in (extra or {}).items():
            if key not in allowed:
                raise ValidationError(
                    f"Unknown field for this directory: {key}"
                )
            setattr(item, key, value)

    async def _by_code(self, model: type, code: str):
        stmt = select(model).where(
            model.code == code, model.is_deleted.is_(False)
        )
        return (await self._session.execute(stmt)).scalars().first()
