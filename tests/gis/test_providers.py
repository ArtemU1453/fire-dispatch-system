"""Unit tests for provider response mapping (mocked HTTP, no network)."""

from __future__ import annotations

import httpx
import pytest

from app.config import get_settings
from app.gis.providers import (
    GeoAccuracy,
    GeocodeQuery,
    GeoProviderError,
    NominatimProvider,
    PhotonProvider,
    create_provider,
)

# --- Nominatim ---------------------------------------------------------------

_NOMINATIM_SEARCH = [
    {
        "lat": "55.7539",
        "lon": "37.6208",
        "display_name": "Красная площадь, Москва, Россия",
        "address": {
            "road": "Красная площадь",
            "house_number": "1",
            "city": "Москва",
            "state": "Москва",
            "country": "Россия",
            "country_code": "ru",
        },
    }
]
_NOMINATIM_REVERSE = {
    "lat": "55.7539",
    "lon": "37.6208",
    "display_name": "1, Красная площадь, Москва, Россия",
    "address": {
        "road": "Красная площадь",
        "house_number": "1",
        "city": "Москва",
        "state": "Москва",
        "country": "Россия",
        "country_code": "ru",
    },
}


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_nominatim_geocode_maps_fields() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/search")
        return httpx.Response(200, json=_NOMINATIM_SEARCH)

    provider = NominatimProvider("http://nominatim.test", client=_client(handler))
    results = await provider.geocode(GeocodeQuery(query="Красная площадь"))
    assert len(results) == 1
    r = results[0]
    assert r.latitude == pytest.approx(55.7539)
    assert r.longitude == pytest.approx(37.6208)
    assert r.accuracy == GeoAccuracy.HOUSE
    assert r.source == "nominatim"


@pytest.mark.asyncio
async def test_nominatim_reverse_maps_components() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/reverse")
        return httpx.Response(200, json=_NOMINATIM_REVERSE)

    provider = NominatimProvider("http://nominatim.test", client=_client(handler))
    result = await provider.reverse(55.7539, 37.6208)
    assert result is not None
    assert result.components.country == "Россия"
    assert result.components.house_number == "1"
    assert result.components.settlement == "Москва"


@pytest.mark.asyncio
async def test_nominatim_http_error_raises_provider_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    provider = NominatimProvider("http://nominatim.test", client=_client(handler))
    with pytest.raises(GeoProviderError):
        await provider.geocode(GeocodeQuery(query="x"))


# --- Photon ------------------------------------------------------------------

_PHOTON_SEARCH = {
    "features": [
        {
            "geometry": {"type": "Point", "coordinates": [37.6208, 55.7539]},
            "properties": {
                "name": "Красная площадь",
                "housenumber": "1",
                "street": "Красная площадь",
                "city": "Москва",
                "state": "Москва",
                "country": "Россия",
                "countrycode": "RU",
            },
        }
    ]
}


@pytest.mark.asyncio
async def test_photon_geocode_maps_geojson() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_PHOTON_SEARCH)

    provider = PhotonProvider("http://photon.test", client=_client(handler))
    results = await provider.geocode(GeocodeQuery(query="Красная площадь"))
    assert results[0].latitude == pytest.approx(55.7539)
    assert results[0].accuracy == GeoAccuracy.HOUSE
    assert results[0].source == "photon"


# --- Factory -----------------------------------------------------------------


def test_factory_unknown_provider_raises() -> None:
    settings = get_settings().model_copy(update={"GIS_PROVIDER": "does-not-exist"})
    with pytest.raises(ValueError):
        create_provider(settings)


def test_factory_builds_fake() -> None:
    settings = get_settings().model_copy(update={"GIS_PROVIDER": "fake"})
    provider = create_provider(settings)
    assert provider.name == "fake"
