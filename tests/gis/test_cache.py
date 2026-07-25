"""Unit tests for the in-memory geocoding cache."""

from __future__ import annotations

import pytest

from app.gis.cache import InMemoryGeoCache
from app.gis.cache.base import NullCache


@pytest.mark.asyncio
async def test_set_and_get() -> None:
    cache = InMemoryGeoCache()
    await cache.set("k", {"v": 1})
    assert await cache.get("k") == {"v": 1}


@pytest.mark.asyncio
async def test_missing_key_returns_none() -> None:
    cache = InMemoryGeoCache()
    assert await cache.get("absent") is None


@pytest.mark.asyncio
async def test_expired_entry_is_evicted() -> None:
    cache = InMemoryGeoCache(default_ttl=0)
    await cache.set("k", 1, ttl=0)
    assert await cache.get("k") is None


@pytest.mark.asyncio
async def test_size_bound_evicts_oldest() -> None:
    cache = InMemoryGeoCache(max_entries=2)
    await cache.set("a", 1)
    await cache.set("b", 2)
    await cache.set("c", 3)  # evicts "a"
    assert await cache.get("a") is None
    assert await cache.get("c") == 3


@pytest.mark.asyncio
async def test_null_cache_never_stores() -> None:
    cache = NullCache()
    await cache.set("k", 1)
    assert await cache.get("k") is None
