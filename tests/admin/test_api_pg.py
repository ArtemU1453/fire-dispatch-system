"""API tests for the administration endpoints (require PostgreSQL)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from .conftest import AdminSeed

pytestmark = pytest.mark.asyncio


async def _create_user(client: AsyncClient, seed: AdminSeed, name: str, **body):
    payload = {
        "username": f"{seed.prefix}-{name}",
        "email": f"{seed.prefix}-{name}@example.com",
        "password": "Str0ngPass1",
        "role_ids": [seed.role_id],
        "actor_name": seed.actor,
        **body,
    }
    return await client.post("/api/v1/admin/users", json=payload)


async def test_user_crud_and_permissions(
    api_client: AsyncClient, seed: AdminSeed
) -> None:
    resp = await _create_user(api_client, seed, "api1")
    assert resp.status_code == 201, resp.text
    user = resp.json()
    assert user["username"] == f"{seed.prefix}-api1"
    assert len(user["roles"]) == 1
    # password never appears in the response
    assert "password" not in user and "hashed_password" not in user
    uid = user["id"]

    got = await api_client.get(f"/api/v1/admin/users/{uid}")
    assert got.status_code == 200

    patched = await api_client.patch(
        f"/api/v1/admin/users/{uid}",
        json={"is_active": False, "actor_name": seed.actor},
    )
    assert patched.json()["is_active"] is False

    perms = await api_client.get(f"/api/v1/admin/users/{uid}/permissions")
    assert f"{seed.prefix}-users.read" in perms.json()


async def test_weak_password_rejected_api(
    api_client: AsyncClient, seed: AdminSeed
) -> None:
    resp = await _create_user(api_client, seed, "weak", password="abc")
    assert resp.status_code == 422


async def test_roles_and_permissions_api(
    api_client: AsyncClient, seed: AdminSeed
) -> None:
    perms = await api_client.get("/api/v1/admin/permissions")
    assert perms.status_code == 200
    codes = {p["code"] for p in perms.json()}
    assert f"{seed.prefix}-users.read" in codes

    resp = await api_client.post(
        "/api/v1/admin/roles",
        json={
            "code": f"{seed.prefix}-viewer", "name": "Наблюдатель",
            "permission_ids": [seed.perm_read_id], "actor_name": seed.actor,
        },
    )
    assert resp.status_code == 201
    assert len(resp.json()["permissions"]) == 1

    roles = await api_client.get("/api/v1/admin/roles")
    assert any(r["code"] == f"{seed.prefix}-viewer" for r in roles.json())


async def test_settings_api_masks_secret(
    api_client: AsyncClient, seed: AdminSeed
) -> None:
    key = f"{seed.prefix}.api.token"
    resp = await api_client.post(
        "/api/v1/admin/settings",
        json={"key": key, "value": "secret-value", "is_secret": True,
              "actor_name": seed.actor},
    )
    assert resp.status_code == 201
    assert resp.json()["value"] == "***"

    upd = await api_client.patch(
        f"/api/v1/admin/settings/{key}",
        json={"value": "new-secret", "actor_name": seed.actor, "reason": "rotate"},
    )
    assert upd.status_code == 200
    assert upd.json()["version"] == 2
    assert upd.json()["value"] == "***"

    hist = await api_client.get(f"/api/v1/admin/settings/{key}/history")
    assert len(hist.json()) == 2
    # even history masks the secret values
    assert all(h["new_value"] in ("***", None) for h in hist.json())


async def test_directories_api(api_client: AsyncClient, seed: AdminSeed) -> None:
    listing = await api_client.get("/api/v1/admin/directories")
    assert listing.status_code == 200
    names = {d["name"] for d in listing.json()}
    assert "resource_types" in names and "organizations" in names

    created = await api_client.post(
        "/api/v1/admin/directories/vehicle_types",
        json={"code": f"{seed.prefix}-AL", "name": "Автолестница",
              "actor_name": seed.actor},
    )
    assert created.status_code == 201
    item = created.json()
    assert item["code"] == f"{seed.prefix}-AL"

    patched = await api_client.patch(
        f"/api/v1/admin/directories/vehicle_types/{item['id']}",
        json={"name": "АЛ-30", "actor_name": seed.actor},
    )
    assert patched.json()["name"] == "АЛ-30"


async def test_integrations_api(api_client: AsyncClient, seed: AdminSeed) -> None:
    resp = await api_client.post(
        "/api/v1/admin/integrations",
        json={
            "code": f"{seed.prefix}-gis", "name": "GIS", "is_enabled": True,
            "secret_ref": "vault://gis/key",
            "configurations": [
                {"key": "url", "value": "https://gis"},
                {"key": "token", "value": "vault://gis/token", "is_secret": True},
            ],
            "actor_name": seed.actor,
        },
    )
    assert resp.status_code == 201, resp.text
    integration = resp.json()
    assert integration["has_secret"] is True
    token_cfg = next(c for c in integration["configurations"] if c["key"] == "token")
    assert token_cfg["value"] == "***"
    iid = integration["id"]

    health = await api_client.post(f"/api/v1/admin/integrations/{iid}/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"

    providers = await api_client.get("/api/v1/admin/integration-providers")
    assert providers.status_code == 200
    assert any(p["code"] == "telephony" for p in providers.json())


async def test_audit_api(api_client: AsyncClient, seed: AdminSeed) -> None:
    await _create_user(api_client, seed, "audited")
    resp = await api_client.get(
        "/api/v1/admin/audit", params={"stream": "users"}
    )
    assert resp.status_code == 200
    rows = resp.json()
    assert any(r["entity_type"] == "user" and r["action"] == "create" for r in rows)


async def test_ai_and_auth_methods_api(api_client: AsyncClient) -> None:
    ai = await api_client.get("/api/v1/admin/ai/providers")
    assert ai.status_code == 200
    body = ai.json()
    assert body["default_provider"] == "mock"
    assert any(p["name"] == "mock" for p in body["providers"])

    methods = await api_client.get("/api/v1/admin/auth-methods")
    assert methods.status_code == 200
    codes = {m["code"] for m in methods.json()}
    assert {"password", "ldap", "oidc"} <= codes
