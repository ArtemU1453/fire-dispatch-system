"""End-to-end API tests for the Dispatch Engine (PostgreSQL).

Covers the REST surface: recommend, preview, retrieval and history, plus request
validation.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient

from .conftest import REF_LAT, REF_LON, DispatchSeed

pytestmark = pytest.mark.asyncio


def _body(seed: DispatchSeed, **overrides) -> dict:
    body = {
        "incident_id": str(uuid4()),
        "incident_type_id": seed.incident_type_id,
        "latitude": REF_LAT,
        "longitude": REF_LON,
    }
    body.update(overrides)
    return body


async def test_recommend_endpoint(
    api_client: AsyncClient, seed: DispatchSeed
) -> None:
    resp = await api_client.post("/api/v1/dispatch/recommend", json=_body(seed))
    assert resp.status_code == 200, resp.text
    rec = resp.json()["recommendation"]
    assert rec["status"] == "recommended"
    assert rec["sufficient"] is True
    assert len(rec["primary_units"]) >= 1
    assert rec["required_capabilities"], "required capabilities must be reported"
    assert all(u["reasons"] for u in rec["primary_units"])


async def test_preview_endpoint_has_no_reserves(
    api_client: AsyncClient, seed: DispatchSeed
) -> None:
    resp = await api_client.post("/api/v1/dispatch/preview", json=_body(seed))
    assert resp.status_code == 200, resp.text
    rec = resp.json()["recommendation"]
    assert rec["is_preview"] is True
    assert rec["reserve_units"] == []


async def test_get_and_history_endpoints(
    api_client: AsyncClient, seed: DispatchSeed
) -> None:
    incident_id = str(uuid4())
    first = await api_client.post(
        "/api/v1/dispatch/recommend", json=_body(seed, incident_id=incident_id)
    )
    assert first.status_code == 200

    got = await api_client.get(f"/api/v1/dispatch/{incident_id}")
    assert got.status_code == 200, got.text
    assert got.json()["incident_id"] == incident_id
    assert got.json()["rule_codes"]

    history = await api_client.get(f"/api/v1/dispatch/history/{incident_id}")
    assert history.status_code == 200
    assert len(history.json()) == 1
    assert history.json()[0]["incident_id"] == incident_id


async def test_get_unknown_incident_is_404(
    api_client: AsyncClient, seed: DispatchSeed
) -> None:
    resp = await api_client.get(f"/api/v1/dispatch/{uuid4()}")
    assert resp.status_code == 404


async def test_missing_location_is_422(
    api_client: AsyncClient, seed: DispatchSeed
) -> None:
    body = {"incident_type_id": seed.incident_type_id}
    resp = await api_client.post("/api/v1/dispatch/recommend", json=body)
    assert resp.status_code == 422


async def test_unknown_incident_type_is_422(
    api_client: AsyncClient, seed: DispatchSeed
) -> None:
    body = _body(seed, incident_type_id=str(uuid4()))
    resp = await api_client.post("/api/v1/dispatch/recommend", json=body)
    assert resp.status_code == 422
