"""Integration tests for the geocoding REST API (ASGI, fake provider)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_normalize_address_endpoint(gis_client: AsyncClient) -> None:
    resp = await gis_client.get(
        "/api/v1/normalize-address", params={"address": "ул Ленина 15"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["normalized"] == "улица ленина, 15"
    assert body["canonical"] == "15 ленина"


@pytest.mark.asyncio
async def test_geocode_endpoint(gis_client: AsyncClient) -> None:
    resp = await gis_client.get(
        "/api/v1/geocode", params={"q": "Красная площадь, Москва", "limit": 1}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert body["results"][0]["latitude"] == pytest.approx(55.753930)
    assert body["provider"] == "fake"


@pytest.mark.asyncio
async def test_coordinates_endpoint(gis_client: AsyncClient) -> None:
    resp = await gis_client.get(
        "/api/v1/coordinates", params={"address": "Дворцовая площадь"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["found"] is True
    assert body["latitude"] == pytest.approx(59.939099)


@pytest.mark.asyncio
async def test_reverse_geocode_endpoint(gis_client: AsyncClient) -> None:
    resp = await gis_client.get(
        "/api/v1/reverse-geocode", params={"lat": 55.75, "lon": 37.62}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["address"]["country"] == "Россия"


@pytest.mark.asyncio
async def test_validate_address_endpoint(gis_client: AsyncClient) -> None:
    resp = await gis_client.get(
        "/api/v1/validate-address", params={"address": "ул Ленина 15"}
    )
    assert resp.status_code == 200
    assert resp.json()["is_valid"] is True


@pytest.mark.asyncio
async def test_reverse_geocode_rejects_out_of_range(gis_client: AsyncClient) -> None:
    resp = await gis_client.get(
        "/api/v1/reverse-geocode", params={"lat": 200, "lon": 0}
    )
    assert resp.status_code == 422
