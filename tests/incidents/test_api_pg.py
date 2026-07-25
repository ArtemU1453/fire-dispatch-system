"""End-to-end API tests for incident management (PostgreSQL)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from .conftest import REF_LAT, REF_LON, IncidentSeed

pytestmark = pytest.mark.asyncio


def _body(seed: IncidentSeed, **overrides) -> dict:
    body = {
        "incident_type_id": seed.incident_type_id,
        "address": "ул. Тверская, 1",
        "latitude": REF_LAT,
        "longitude": REF_LON,
        "actor_name": "Диспетчер",
    }
    body.update(overrides)
    return body


async def _create(api_client: AsyncClient, seed: IncidentSeed) -> dict:
    resp = await api_client.post("/api/v1/incidents", json=_body(seed))
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_create_and_get(api_client: AsyncClient, seed: IncidentSeed) -> None:
    created = await _create(api_client, seed)
    assert created["number"].startswith("INC-")
    assert created["status"] == "created"
    assert "checking" in created["allowed_transitions"]

    got = await api_client.get(f"/api/v1/incidents/{created['id']}")
    assert got.status_code == 200
    assert len(got.json()["timeline"]) >= 1


async def test_update_and_history(
    api_client: AsyncClient, seed: IncidentSeed
) -> None:
    created = await _create(api_client, seed)
    resp = await api_client.put(
        f"/api/v1/incidents/{created['id']}",
        json={"priority": "critical", "actor_name": "Д"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["priority"] == "critical"
    assert any(h["field"] == "priority" for h in body["history"])


async def test_status_transition_valid_and_invalid(
    api_client: AsyncClient, seed: IncidentSeed
) -> None:
    created = await _create(api_client, seed)
    ok = await api_client.patch(
        f"/api/v1/incidents/{created['id']}/status", json={"status": "checking"}
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["status"] == "checking"

    bad = await api_client.patch(
        f"/api/v1/incidents/{created['id']}/status", json={"status": "completed"}
    )
    assert bad.status_code == 422


async def test_timeline_and_comments(
    api_client: AsyncClient, seed: IncidentSeed
) -> None:
    created = await _create(api_client, seed)
    comment = await api_client.post(
        f"/api/v1/incidents/{created['id']}/comments",
        json={"text": "Проверить информацию", "author_name": "Д"},
    )
    assert comment.status_code == 201, comment.text
    assert comment.json()["text"] == "Проверить информацию"

    timeline = await api_client.get(f"/api/v1/incidents/{created['id']}/timeline")
    assert timeline.status_code == 200
    kinds = {e["event_type"] for e in timeline.json()["entries"]}
    assert "created" in kinds and "comment_added" in kinds


async def test_assign_units_and_recommend(
    api_client: AsyncClient, seed: IncidentSeed
) -> None:
    created = await _create(api_client, seed)
    units = await api_client.post(
        f"/api/v1/incidents/{created['id']}/units",
        json={"units": [{"resource_id": seed.resource_id, "role": "primary"}]},
    )
    assert units.status_code == 200, units.text
    assert len(units.json()["dispatches"]) == 1

    rec = await api_client.post(f"/api/v1/incidents/{created['id']}/recommend")
    assert rec.status_code == 200, rec.text
    assert len(rec.json()["recommendations"]) == 1


async def test_active_and_archive_endpoints(
    api_client: AsyncClient, seed: IncidentSeed
) -> None:
    created = await _create(api_client, seed)
    incident_id = created["id"]
    await api_client.patch(
        f"/api/v1/incidents/{incident_id}/status", json={"status": "cancelled"}
    )

    active = await api_client.get("/api/v1/incidents/active")
    archive = await api_client.get("/api/v1/incidents/archive")
    assert active.status_code == 200 and archive.status_code == 200
    assert incident_id not in {i["id"] for i in active.json()}
    assert incident_id in {i["id"] for i in archive.json()}
