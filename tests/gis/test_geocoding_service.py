"""Integration tests for the geocoding service (fake provider, sqlite log)."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.gis.cache import InMemoryGeoCache
from app.gis.models import GeocodingLog
from app.gis.providers.base import (
    GeocodeQuery,
    GeoProvider,
    GeoProviderError,
    ReverseResult,
)
from app.gis.services.geocoding import GeocodingService


@pytest.mark.asyncio
async def test_geocode_returns_results_with_normalized_address(
    geocoding_service,
) -> None:
    outcome = await geocoding_service.geocode("Красная площадь, Москва")
    assert outcome.success and outcome.results
    assert outcome.results[0].normalized_address == outcome.normalized_address
    assert outcome.provider == "fake"


@pytest.mark.asyncio
async def test_geocode_second_call_is_cached(geocoding_service) -> None:
    first = await geocoding_service.geocode("Красная площадь")
    second = await geocoding_service.geocode("Красная площадь")
    assert first.from_cache is False
    assert second.from_cache is True
    assert second.results[0].latitude == first.results[0].latitude


@pytest.mark.asyncio
async def test_reverse_returns_components(geocoding_service) -> None:
    outcome = await geocoding_service.reverse(55.75, 37.62)
    assert outcome.success and outcome.result is not None
    assert outcome.result.components.country == "Россия"


@pytest.mark.asyncio
async def test_validate_true_for_known_place(geocoding_service) -> None:
    outcome = await geocoding_service.validate("ул Ленина 15")
    assert outcome.is_valid is True
    assert outcome.best_match is not None


@pytest.mark.asyncio
async def test_geocode_logs_request(geocoding_service, log_session_factory) -> None:
    await geocoding_service.geocode("Красная площадь")
    async with log_session_factory() as session:
        count = await session.scalar(select(func.count()).select_from(GeocodingLog))
        row = (await session.execute(select(GeocodingLog))).scalars().first()
    assert count == 1
    assert row.operation == "geocode"
    assert row.provider == "fake"
    assert row.success is True
    assert row.response_time_ms is not None


class _FailingProvider(GeoProvider):
    name = "failing"

    async def geocode(self, query: GeocodeQuery):  # noqa: ANN001
        raise GeoProviderError("upstream down")

    async def reverse(
        self, latitude, longitude, *, language=None
    ) -> ReverseResult | None:
        raise GeoProviderError("upstream down")


@pytest.mark.asyncio
async def test_provider_failure_is_handled_and_logged(log_session_factory) -> None:
    service = GeocodingService(
        provider=_FailingProvider(),
        cache=InMemoryGeoCache(),
        log_session_factory=log_session_factory,
    )
    outcome = await service.geocode("anywhere")
    assert outcome.success is False
    assert outcome.error == "upstream down"
    async with log_session_factory() as session:
        row = (await session.execute(select(GeocodingLog))).scalars().first()
    assert row.success is False
    assert "upstream down" in row.error
