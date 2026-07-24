"""Tests for the health-check endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_ok(client: AsyncClient) -> None:
    """``GET /health`` returns 200 with an ``ok`` status and DB ``up``."""
    response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "up"
    assert "version" in body
    assert "app" in body


@pytest.mark.asyncio
async def test_health_versioned_route(client: AsyncClient) -> None:
    """The health endpoint is also served under the versioned API prefix."""
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_openapi_available(client: AsyncClient) -> None:
    """The OpenAPI schema is generated and served."""
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"]
