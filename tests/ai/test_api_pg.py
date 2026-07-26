"""API tests for the AI-platform endpoints (require PostgreSQL)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from .conftest import AISeed

pytestmark = pytest.mark.asyncio


async def test_transcribe_endpoint(api_client: AsyncClient, seed: AISeed) -> None:
    resp = await api_client.post(
        "/api/v1/ai/transcribe",
        json={"sample_text": seed.call_text, "call_id": seed.call_id},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["text"] == seed.call_text
    assert body["segments"]
    assert body["meta"]["provider"] == "mock"


async def test_extract_endpoint(api_client: AsyncClient, seed: AISeed) -> None:
    resp = await api_client.post(
        "/api/v1/ai/extract", json={"text": seed.call_text}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["advisory"] is True
    assert body["entities"]["phone"] == "+7 999 123 45 67"
    assert "многоквартирный жилой дом" in body["entities"]["objects"]


async def test_classify_endpoint(api_client: AsyncClient, seed: AISeed) -> None:
    resp = await api_client.post(
        "/api/v1/ai/classify", json={"text": seed.call_text}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["category"] == "fire"
    assert body["priority"] == "critical"
    assert body["advisory"] is True
    assert body["meta"]["model_version"] == "1.0.0"


async def test_summarize_endpoint(api_client: AsyncClient, seed: AISeed) -> None:
    resp = await api_client.post(
        "/api/v1/ai/summarize", json={"text": seed.call_text}
    )
    assert resp.status_code == 200
    assert "пожар" in resp.json()["summary"].lower()


async def test_analyze_endpoint(api_client: AsyncClient, seed: AISeed) -> None:
    resp = await api_client.post(
        "/api/v1/ai/analyze", json={"text": seed.call_text}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"]
    assert body["entities"]["address"] is not None
    assert body["classification"]["category"] == "fire"


async def test_analyze_call_endpoint(api_client: AsyncClient, seed: AISeed) -> None:
    resp = await api_client.post(
        f"/api/v1/ai/calls/{seed.call_id}/analyze", json={}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["classification"]["category"] == "fire"
    assert body["entities"]["phone"] == "+7 999 123 45 67"


async def test_providers_endpoint(api_client: AsyncClient) -> None:
    resp = await api_client.get("/api/v1/ai/providers")
    assert resp.status_code == 200
    body = resp.json()
    assert body["default"] == "mock"
    names = {p["name"] for p in body["providers"]}
    assert "mock" in names
    mock = next(p for p in body["providers"] if p["name"] == "mock")
    assert mock["is_default"] is True
    assert "transcribe" in mock["capabilities"]


async def test_health_endpoint(api_client: AsyncClient) -> None:
    resp = await api_client.get("/api/v1/ai/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["healthy"] is True
    assert body["providers"]


async def test_audit_endpoint_records_calls(
    api_client: AsyncClient, seed: AISeed
) -> None:
    # Make a couple of AI calls, then read the audit log back.
    await api_client.post("/api/v1/ai/classify", json={"text": seed.call_text})
    await api_client.post(
        f"/api/v1/ai/calls/{seed.call_id}/analyze", json={}
    )
    resp = await api_client.get("/api/v1/ai/audit")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) >= 2
    capabilities = {r["capability"] for r in rows}
    assert "classify_incident" in capabilities
    assert "analyze" in capabilities
    # audit records model metadata, never prompt text
    assert all("text" not in r for r in rows)
    assert all(r["provider"] == "mock" for r in rows)


async def test_analyze_call_missing_text_returns_422(
    api_client: AsyncClient, seed: AISeed
) -> None:
    # Register a bare call (no transcript) via the calls API, then analyze it.
    created = await api_client.post("/api/v1/calls", json={})
    call_id = created.json()["id"]
    resp = await api_client.post(
        f"/api/v1/ai/calls/{call_id}/analyze", json={}
    )
    assert resp.status_code == 422
