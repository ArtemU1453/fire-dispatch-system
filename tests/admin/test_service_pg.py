"""Integration tests for admin services (require PostgreSQL)."""

from __future__ import annotations

from uuid import UUID

import pytest

from app.admin.rbac import RBACService
from app.admin.schemas.admin import (
    DirectoryItemCreate,
    DirectoryItemUpdate,
    IntegrationCreate,
    RoleCreate,
    SettingCreate,
    SettingUpdate,
    UserCreate,
    UserUpdate,
)
from app.admin.services import (
    AuditService,
    DirectoryService,
    IntegrationService,
    RoleService,
    SettingsService,
    UserService,
)
from app.core.exceptions import ValidationError
from app.models.enums import AuditAction

from .conftest import AdminSeed

pytestmark = pytest.mark.asyncio


async def _make_user(s, seed: AdminSeed, name: str, *, role_ids=None, **kw):
    if role_ids is None:
        role_ids = [UUID(seed.role_id)]
    return await UserService(s).create_user(
        UserCreate(
            username=f"{seed.prefix}-{name}",
            email=f"{seed.prefix}-{name}@example.com",
            password="Str0ngPass1",
            role_ids=role_ids,
            actor_name=seed.actor,
            **kw,
        )
    )


async def test_create_user_and_rbac(pg_factory, seed: AdminSeed) -> None:
    async with pg_factory() as s:
        user = await _make_user(s, seed, "u1")
        assert user.hashed_password.startswith("pbkdf2_sha256$")
        await s.commit()
        uid = user.id

    async with pg_factory() as s:
        rbac = RBACService(s)
        perms = await rbac.effective_permissions(uid)
        assert f"{seed.prefix}-users.read" in perms
        assert f"{seed.prefix}-users.write" in perms
        assert await rbac.has_permission(uid, f"{seed.prefix}-users.read") is True
        assert await rbac.has_permission(uid, "nope") is False


async def test_superuser_has_all_permissions(pg_factory, seed: AdminSeed) -> None:
    async with pg_factory() as s:
        user = await _make_user(s, seed, "super", is_superuser=True, role_ids=[])
        await s.commit()
        uid = user.id

    async with pg_factory() as s:
        rbac = RBACService(s)
        assert await rbac.has_permission(uid, "anything.at.all") is True


async def test_weak_password_rejected(pg_factory, seed: AdminSeed) -> None:
    async with pg_factory() as s:
        with pytest.raises(ValidationError):
            await UserService(s).create_user(
                UserCreate(
                    username=f"{seed.prefix}-weak",
                    email=f"{seed.prefix}-weak@example.com",
                    password="abc",  # violates seeded policy
                    actor_name=seed.actor,
                )
            )


async def test_update_user_audited(pg_factory, seed: AdminSeed) -> None:
    async with pg_factory() as s:
        user = await _make_user(s, seed, "u2")
        await s.commit()
        uid = user.id

    async with pg_factory() as s:
        updated = await UserService(s).update_user(
            uid, UserUpdate(is_active=False, actor_name=seed.actor,
                            reason="отключение по запросу")
        )
        assert updated.is_active is False
        await s.commit()

    async with pg_factory() as s:
        rows = await AuditService(s).list_audit(entity_type="user", entity_id=uid)
        assert any(r.action is AuditAction.UPDATE for r in rows)
        upd = next(r for r in rows if r.action is AuditAction.UPDATE)
        assert upd.changes["is_active"] == {"old": True, "new": False}
        assert upd.changes["_reason"] == "отключение по запросу"


async def test_role_create_and_update(pg_factory, seed: AdminSeed) -> None:
    async with pg_factory() as s:
        role = await RoleService(s).create_role(
            RoleCreate(
                code=f"{seed.prefix}-r2", name="Оператор",
                permission_ids=[UUID(seed.perm_read_id)], actor_name=seed.actor,
            )
        )
        assert len([link for link in role.permission_links if not link.is_deleted]) == 1
        await s.commit()
        rid = role.id

    async with pg_factory() as s:
        from app.admin.schemas.admin import RoleUpdate

        role = await RoleService(s).update_role(
            rid, RoleUpdate(
                permission_ids=[UUID(seed.perm_read_id), UUID(seed.perm_write_id)],
                actor_name=seed.actor,
            )
        )
        live = [link for link in role.permission_links if not link.is_deleted]
        assert len(live) == 2


async def test_settings_versioning_and_history(pg_factory, seed: AdminSeed) -> None:
    key = f"{seed.prefix}.maps.token"
    async with pg_factory() as s:
        svc = SettingsService(s)
        setting = await svc.create_setting(
            SettingCreate(key=key, value="v1", actor_name=seed.actor)
        )
        assert setting.version == 1
        await svc.update_setting(
            key, SettingUpdate(value="v2", actor_name=seed.actor, reason="ротация")
        )
        await s.commit()

    async with pg_factory() as s:
        svc = SettingsService(s)
        setting = await svc.get_setting(key)
        assert setting.version == 2
        assert setting.value == "v2"
        history = await svc.history(key)
        assert len(history) == 2
        assert history[0].new_value == "v2"


async def test_settings_type_validation(pg_factory, seed: AdminSeed) -> None:
    from app.admin.models.enums import SettingType

    async with pg_factory() as s:
        with pytest.raises(ValidationError):
            await SettingsService(s).create_setting(
                SettingCreate(
                    key=f"{seed.prefix}.timeout", value="notanint",
                    value_type=SettingType.INTEGER, actor_name=seed.actor,
                )
            )


async def test_directory_create_and_update(pg_factory, seed: AdminSeed) -> None:
    async with pg_factory() as s:
        svc = DirectoryService(s)
        item = await svc.create_item(
            "resource_types",
            DirectoryItemCreate(
                code=f"{seed.prefix}-VT", name="Автоцистерна",
                extra={"category": "vehicle"}, actor_name=seed.actor,
            ),
        )
        assert getattr(item.category, "value", item.category) == "vehicle"
        await s.commit()
        item_id = item.id

    async with pg_factory() as s:
        svc = DirectoryService(s)
        updated = await svc.update_item(
            "resource_types", item_id,
            DirectoryItemUpdate(name="АЦ-40", actor_name=seed.actor),
        )
        assert updated.name == "АЦ-40"


async def test_directory_rejects_unknown_field(pg_factory, seed: AdminSeed) -> None:
    async with pg_factory() as s:
        with pytest.raises(ValidationError):
            await DirectoryService(s).create_item(
                "vehicle_types",
                DirectoryItemCreate(
                    code=f"{seed.prefix}-X", name="X",
                    extra={"nonexistent": 1}, actor_name=seed.actor,
                ),
            )


async def test_integration_secret_masking_and_health(
    pg_factory, seed: AdminSeed
) -> None:
    from app.admin.schemas.admin import IntegrationConfigInput

    async with pg_factory() as s:
        svc = IntegrationService(s)
        integration = await svc.create_integration(
            IntegrationCreate(
                code=f"{seed.prefix}-sms", name="SMS", is_enabled=True,
                secret_ref="vault://sms/token",
                configurations=[
                    IntegrationConfigInput(key="url", value="https://sms"),
                    IntegrationConfigInput(
                        key="api_key", value="vault://sms/key", is_secret=True
                    ),
                ],
                actor_name=seed.actor,
            )
        )
        await s.commit()
        iid = integration.id

    async with pg_factory() as s:
        svc = IntegrationService(s)
        check = await svc.health_check(iid)
        assert check.status.value == "healthy"
        await s.commit()

    async with pg_factory() as s:
        svc = IntegrationService(s)
        integration = await svc.get_integration(iid)
        assert integration.status.value == "active"
        # the secret config value is still a reference, never a plaintext secret
        secret_cfg = next(
            c for c in integration.configurations if c.key == "api_key"
        )
        assert secret_cfg.value == "vault://sms/key"
        assert secret_cfg.is_secret is True
