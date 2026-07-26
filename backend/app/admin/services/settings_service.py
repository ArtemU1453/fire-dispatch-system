"""System settings management (stage §4).

A universal, typed and categorised settings store. Every setting has a key,
value, type, description, category, **version** and an append-only **change
history** (old → new, who, when, why). Changing a setting bumps its version,
writes a history row and an audit entry.
"""

from __future__ import annotations

import json
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.audit import AdminAuditRecorder
from app.admin.models.entities import Setting, SettingHistory
from app.admin.models.enums import SettingCategory, SettingType
from app.admin.schemas.admin import SettingCreate, SettingUpdate
from app.admin.utils.actor import Actor
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.enums import AuditAction


def parse_value(value: str | None, value_type: SettingType):
    """Parse a raw string into its typed value (raises on mismatch)."""
    if value is None:
        return None
    try:
        if value_type is SettingType.INTEGER:
            return int(value)
        if value_type is SettingType.NUMBER:
            return float(value)
        if value_type is SettingType.BOOLEAN:
            return value.strip().lower() in {"true", "1", "yes", "on"}
        if value_type is SettingType.JSON:
            return json.loads(value)
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValidationError(
            f"Значение не соответствует типу {value_type.value}: {exc}"
        ) from exc
    return value


class SettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AdminAuditRecorder(session)

    async def list_settings(
        self, *, category: SettingCategory | None = None
    ) -> Sequence[Setting]:
        stmt = select(Setting).where(Setting.is_deleted.is_(False))
        if category is not None:
            stmt = stmt.where(Setting.category == category)
        stmt = stmt.order_by(Setting.category, Setting.key)
        return (await self._session.execute(stmt)).scalars().all()

    async def get_setting(self, key: str) -> Setting:
        setting = await self._by_key(key)
        if setting is None:
            raise NotFoundError(f"Setting not found: {key}")
        return setting

    async def typed_value(self, key: str):
        setting = await self.get_setting(key)
        return parse_value(setting.value, setting.value_type)

    async def create_setting(self, data: SettingCreate) -> Setting:
        if await self._by_key(data.key) is not None:
            raise ConflictError(f"Setting already exists: {data.key}")
        parse_value(data.value, data.value_type)  # validate
        actor = Actor(name=data.actor_name)
        setting = Setting(
            key=data.key,
            value=data.value,
            value_type=data.value_type,
            category=data.category,
            description=data.description,
            is_secret=data.is_secret,
            version=1,
        )
        self._session.add(setting)
        await self._session.flush()
        self._history(setting, None, data.value, actor, data.reason)
        self._audit.record(
            AuditAction.CREATE, "setting", entity_id=setting.id,
            changes={"key": data.key, "category": data.category.value},
            reason=data.reason, actor=actor,
        )
        await self._session.flush()
        return await self.get_setting(data.key)

    async def update_setting(self, key: str, data: SettingUpdate) -> Setting:
        setting = await self.get_setting(key)
        actor = Actor(name=data.actor_name)
        changes: dict = {}

        if data.value is not None and data.value != setting.value:
            parse_value(data.value, setting.value_type)  # validate
            old = setting.value
            setting.version += 1
            setting.value = data.value
            self._history(setting, old, data.value, actor, data.reason)
            changes["value"] = {
                "old": self._mask(setting, old),
                "new": self._mask(setting, data.value),
            }
        if data.description is not None and data.description != setting.description:
            changes["description"] = {
                "old": setting.description, "new": data.description
            }
            setting.description = data.description
        if data.is_active is not None and data.is_active != setting.is_active:
            changes["is_active"] = {
                "old": setting.is_active, "new": data.is_active
            }
            setting.is_active = data.is_active

        if changes:
            self._audit.record(
                AuditAction.UPDATE, "setting", entity_id=setting.id,
                changes=changes, reason=data.reason, actor=actor,
            )
        await self._session.flush()
        return await self.get_setting(key)

    async def history(self, key: str) -> Sequence[SettingHistory]:
        stmt = (
            select(SettingHistory)
            .where(SettingHistory.key == key)
            .order_by(SettingHistory.version.desc())
        )
        return (await self._session.execute(stmt)).scalars().all()

    # ------------------------------------------------------------ helpers
    def _history(self, setting, old, new, actor: Actor, reason) -> None:
        # Never persist a secret value — the history keeps only a mask for it.
        self._session.add(
            SettingHistory(
                setting_id=setting.id,
                key=setting.key,
                old_value=self._mask(setting, old),
                new_value=self._mask(setting, new),
                version=setting.version,
                changed_by_user_id=actor.user_id,
                changed_by_name=actor.name,
                reason=reason,
            )
        )

    @staticmethod
    def _mask(setting: Setting, value):
        if value is None:
            return None
        return "***" if setting.is_secret else value

    async def _by_key(self, key: str) -> Setting | None:
        stmt = select(Setting).where(
            Setting.key == key, Setting.is_deleted.is_(False)
        )
        return (await self._session.execute(stmt)).scalars().first()
