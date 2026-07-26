"""API tests for the resource-management endpoints (require PostgreSQL)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from .conftest import ResourceSeed

pytestmark = pytest.mark.asyncio


async def test_list_units(api_client: AsyncClient, seed: ResourceSeed) -> None:
    resp = await api_client.get("/api/v1/units")
    assert resp.status_code == 200
    codes = {u["code"] for u in resp.json()}
    assert f"{seed.prefix}-U1" in codes


async def test_get_unit(api_client: AsyncClient, seed: ResourceSeed) -> None:
    resp = await api_client.get(f"/api/v1/units/{seed.unit_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == f"{seed.prefix}-U1"
    assert body["status"]["code"] == "free"
    assert body["is_available"] is True


async def test_update_unit_status(
    api_client: AsyncClient, seed: ResourceSeed
) -> None:
    resp = await api_client.patch(
        f"/api/v1/units/{seed.unit_id}/status",
        json={"status_code": "on_scene", "actor_name": "tester"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"]["code"] == "on_scene"
    assert body["is_available"] is False

    # The vehicle the Dispatch Engine reads followed the unit.
    veh = await api_client.get(f"/api/v1/vehicles/{seed.vehicle_resource_id}")
    assert veh.json()["status"]["code"] == "on_scene"


async def test_update_unit_status_unknown_code(
    api_client: AsyncClient, seed: ResourceSeed
) -> None:
    resp = await api_client.patch(
        f"/api/v1/units/{seed.unit_id}/status",
        json={"status_code": "does_not_exist"},
    )
    assert resp.status_code == 422


async def test_list_and_get_vehicles(
    api_client: AsyncClient, seed: ResourceSeed
) -> None:
    resp = await api_client.get("/api/v1/vehicles")
    assert resp.status_code == 200
    assert any(v["code"] == f"{seed.prefix}-VEH" for v in resp.json())

    one = await api_client.get(f"/api/v1/vehicles/{seed.vehicle_resource_id}")
    assert one.status_code == 200
    assert one.json()["plate_number"] == "А001АА"


async def test_update_vehicle_status(
    api_client: AsyncClient, seed: ResourceSeed
) -> None:
    resp = await api_client.patch(
        f"/api/v1/vehicles/{seed.vehicle_resource_id}/status",
        json={"status_code": "repair"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"]["code"] == "repair"


async def test_list_crews(api_client: AsyncClient, seed: ResourceSeed) -> None:
    resp = await api_client.get("/api/v1/crews")
    assert resp.status_code == 200
    crew = next(c for c in resp.json() if c["code"] == f"{seed.prefix}-C1")
    assert crew["member_count"] == 1
    assert crew["members"][0]["is_commander"] is True


async def test_list_personnel(
    api_client: AsyncClient, seed: ResourceSeed
) -> None:
    resp = await api_client.get("/api/v1/personnel")
    assert resp.status_code == 200
    person = next(
        p for p in resp.json() if p["code"] == f"{seed.prefix}-PER"
    )
    assert person["full_name"] == "Иванов Иван"
    assert person["rank"] == "сержант"


async def test_resources_status_overview(
    api_client: AsyncClient, seed: ResourceSeed
) -> None:
    resp = await api_client.get("/api/v1/resources/status")
    assert resp.status_code == 200
    items = resp.json()
    codes = {i["status"]["code"] for i in items}
    # All 9 seeded statuses present (not shadowed by search's /resources/{id}).
    assert {"free", "on_scene", "repair", "reserve"} <= codes


async def test_resources_history(
    api_client: AsyncClient, seed: ResourceSeed
) -> None:
    await api_client.patch(
        f"/api/v1/units/{seed.unit_id}/status",
        json={"status_code": "enroute"},
    )
    resp = await api_client.get(
        "/api/v1/resources/history", params={"unit_id": seed.unit_id}
    )
    assert resp.status_code == 200
    rows = resp.json()
    assert rows
    assert rows[0]["to_value"] == "enroute"
    assert rows[0]["event_type"] == "unit_status_changed"
