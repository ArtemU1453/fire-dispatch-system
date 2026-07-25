"""API tests for resource search against PostGIS (skip if no DB)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

REF = {"lat": 55.7539, "lon": 37.6208}


async def test_nearest_orders_by_distance(api_client: AsyncClient, seed) -> None:
    resp = await api_client.get(
        "/api/v1/resources/nearest", params={**REF, "categories": "vehicle", "limit": 5}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert [i["name"] for i in body["items"]] == ["NEAR", "MID", "FAR"]
    assert body["items"][0]["distance_meters"] < body["items"][1]["distance_meters"]
    assert body["reference_point"] == {"latitude": 55.7539, "longitude": 37.6208}


async def test_radius_excludes_far(api_client: AsyncClient, seed) -> None:
    resp = await api_client.get(
        "/api/v1/resources/radius", params={**REF, "radius_m": 5000}
    )
    assert resp.status_code == 200
    names = {i["name"] for i in resp.json()["items"]}
    # All near objects (incl. the hydrant ~300 m away) are in range; FAR is not.
    assert names == {"NEAR", "MID", "HYDRANT"}
    assert "FAR" not in names


async def test_search_filter_sort_paginate(api_client: AsyncClient, seed) -> None:
    resp = await api_client.get(
        "/api/v1/resources/search",
        params=[("categories", "vehicle"), ("sort", "-name"), ("limit", "2")],
    )
    body = resp.json()
    assert body["total"] == 3
    assert [i["name"] for i in body["items"]] == ["NEAR", "MID"]  # desc name, page 1


async def test_search_result_is_cached(api_client: AsyncClient, seed) -> None:
    params = [("categories", "vehicle"), ("sort", "name")]
    first = await api_client.get("/api/v1/resources/search", params=params)
    second = await api_client.get("/api/v1/resources/search", params=params)
    assert first.json()["from_cache"] is False
    assert second.json()["from_cache"] is True


async def test_filter_by_capability(api_client: AsyncClient, seed) -> None:
    resp = await api_client.get(
        "/api/v1/resources/filter", params={"capability_ids": str(seed.capability_id)}
    )
    assert [i["name"] for i in resp.json()["items"]] == ["NEAR"]


async def test_get_by_id(api_client: AsyncClient, seed) -> None:
    resp = await api_client.get(f"/api/v1/resources/{seed.near_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "NEAR"


async def test_get_by_id_404(api_client: AsyncClient, seed) -> None:
    resp = await api_client.get(
        "/api/v1/resources/00000000-0000-0000-0000-000000000000"
    )
    assert resp.status_code == 404


async def test_nearest_without_location_is_422(api_client: AsyncClient, seed) -> None:
    resp = await api_client.get("/api/v1/resources/nearest")
    assert resp.status_code == 422


async def test_unknown_sort_field_is_422(api_client: AsyncClient, seed) -> None:
    resp = await api_client.get(
        "/api/v1/resources/search", params={"sort": "nonsense"}
    )
    assert resp.status_code == 422
