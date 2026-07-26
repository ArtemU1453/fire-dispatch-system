"""API tests for the call-management endpoints (require PostgreSQL)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from .conftest import CallSeed

pytestmark = pytest.mark.asyncio


async def _create(client: AsyncClient, **body) -> dict:
    resp = await client.post("/api/v1/calls", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_create_and_get_call(api_client: AsyncClient) -> None:
    call = await _create(
        api_client, caller_number="+70001112233", notes="Задымление"
    )
    assert call["status"] == "new"
    assert call["number"].startswith("CALL-")
    assert call["queue"] is not None
    assert call["queue"]["status"] == "waiting"

    got = await api_client.get(f"/api/v1/calls/{call['id']}")
    assert got.status_code == 200
    assert got.json()["caller_number"] == "+70001112233"


async def test_list_calls(api_client: AsyncClient) -> None:
    await _create(api_client, notes="one")
    resp = await api_client.get("/api/v1/calls")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


async def test_change_status(api_client: AsyncClient) -> None:
    call = await _create(api_client)
    resp = await api_client.patch(
        f"/api/v1/calls/{call['id']}/status",
        json={"status": "accepted", "actor_name": "tester"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "accepted"
    assert body["answered_at"] is not None


async def test_change_status_invalid_returns_422(api_client: AsyncClient) -> None:
    call = await _create(api_client)
    resp = await api_client.patch(
        f"/api/v1/calls/{call['id']}/status", json={"status": "completed"}
    )
    assert resp.status_code == 422


async def test_incident_create_via_api(
    api_client: AsyncClient, seed: CallSeed
) -> None:
    call = await _create(api_client, notes="Пожар")
    resp = await api_client.post(
        f"/api/v1/calls/{call['id']}/incident",
        json={
            "create": True,
            "incident_type_id": seed.incident_type_id,
            "category": "fire",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "linked"
    assert body["incident_id"] is not None
    assert body["links"][0]["link_type"] == "created"


async def test_incident_link_existing_via_api(
    api_client: AsyncClient, seed: CallSeed
) -> None:
    call = await _create(api_client)
    resp = await api_client.post(
        f"/api/v1/calls/{call['id']}/incident",
        json={"incident_id": seed.incident_id},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["incident_id"] == seed.incident_id
    assert body["links"][0]["link_type"] == "linked"


async def test_incident_ambiguous_choice_returns_422(
    api_client: AsyncClient, seed: CallSeed
) -> None:
    call = await _create(api_client)
    resp = await api_client.post(
        f"/api/v1/calls/{call['id']}/incident",
        json={"incident_id": seed.incident_id, "create": True},
    )
    assert resp.status_code == 422


async def test_queue_endpoint(api_client: AsyncClient) -> None:
    await _create(api_client, priority="critical", notes="urgent")
    await _create(api_client, priority="low", notes="minor")
    resp = await api_client.get("/api/v1/calls/queue")
    assert resp.status_code == 200
    entries = resp.json()
    assert len(entries) >= 2
    # denormalized fields present for the dispatcher board
    assert entries[0]["call_number"] is not None
    assert "wait_seconds" in entries[0]
    # most urgent first
    assert entries[0]["priority"] == "critical"


async def test_assign_dispatcher_endpoint(api_client: AsyncClient) -> None:
    call = await _create(api_client)
    resp = await api_client.post(
        f"/api/v1/calls/{call['id']}/assign",
        json={"dispatcher_name": "Диспетчер-2", "workstation": "WS-2"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["dispatcher_name"] == "Диспетчер-2"
    assert body["queue"]["status"] == "assigned"


async def test_history_endpoint(api_client: AsyncClient) -> None:
    call = await _create(api_client)
    await api_client.patch(
        f"/api/v1/calls/{call['id']}/status", json={"status": "accepted"}
    )
    resp = await api_client.get(
        "/api/v1/calls/history", params={"call_id": call["id"]}
    )
    assert resp.status_code == 200
    rows = resp.json()
    assert any(r["event_type"] == "created" for r in rows)
    assert any(r["to_status"] == "accepted" for r in rows)


async def test_provider_health_endpoint(api_client: AsyncClient) -> None:
    resp = await api_client.get("/api/v1/calls/provider/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["healthy"] is True
    assert body["provider"] == "mock"


async def test_provider_answer_end_flow(api_client: AsyncClient) -> None:
    call = await _create(api_client, register_with_provider=True)
    assert call["status"] == "ringing"
    assert call["external_id"] is not None

    answered = await api_client.post(f"/api/v1/calls/{call['id']}/answer")
    assert answered.status_code == 200
    assert answered.json()["status"] == "accepted"

    ended = await api_client.post(f"/api/v1/calls/{call['id']}/end")
    assert ended.status_code == 200
    assert ended.json()["status"] == "completed"
