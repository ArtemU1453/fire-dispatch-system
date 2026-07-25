"""Provider factory — selects a :class:`GeoProvider` from configuration.

The only place that knows about concrete providers. Everything else depends on
the :class:`GeoProvider` interface, so adding Google / Yandex later means adding
a class and a registry entry here — nothing else changes (Open/Closed).
"""

from __future__ import annotations

from collections.abc import Callable

from app.config import Settings, get_settings
from app.gis.providers.arcgis import ArcGISProvider
from app.gis.providers.base import GeoProvider
from app.gis.providers.fake import FakeGeoProvider
from app.gis.providers.nominatim import NominatimProvider
from app.gis.providers.pelias import PeliasProvider
from app.gis.providers.photon import PhotonProvider


def _build_nominatim(s: Settings) -> GeoProvider:
    return NominatimProvider(
        s.GIS_NOMINATIM_URL, timeout=s.GIS_HTTP_TIMEOUT, user_agent=s.GIS_USER_AGENT
    )


def _build_photon(s: Settings) -> GeoProvider:
    return PhotonProvider(
        s.GIS_PHOTON_URL, timeout=s.GIS_HTTP_TIMEOUT, user_agent=s.GIS_USER_AGENT
    )


def _build_pelias(s: Settings) -> GeoProvider:
    return PeliasProvider(
        s.GIS_PELIAS_URL,
        timeout=s.GIS_HTTP_TIMEOUT,
        user_agent=s.GIS_USER_AGENT,
        api_key=s.GIS_PELIAS_API_KEY,
    )


def _build_arcgis(s: Settings) -> GeoProvider:
    return ArcGISProvider(
        s.GIS_ARCGIS_URL,
        timeout=s.GIS_HTTP_TIMEOUT,
        user_agent=s.GIS_USER_AGENT,
        token=s.GIS_ARCGIS_TOKEN,
    )


def _build_fake(_: Settings) -> GeoProvider:
    return FakeGeoProvider()


#: Registry of known providers. Extend to add Google / Yandex.
PROVIDER_REGISTRY: dict[str, Callable[[Settings], GeoProvider]] = {
    "nominatim": _build_nominatim,
    "photon": _build_photon,
    "pelias": _build_pelias,
    "arcgis": _build_arcgis,
    "fake": _build_fake,
}


def create_provider(settings: Settings | None = None) -> GeoProvider:
    """Instantiate the configured :class:`GeoProvider`."""
    settings = settings or get_settings()
    key = settings.GIS_PROVIDER.strip().lower()
    builder = PROVIDER_REGISTRY.get(key)
    if builder is None:
        raise ValueError(
            f"Unknown GIS_PROVIDER {settings.GIS_PROVIDER!r}; "
            f"available: {', '.join(sorted(PROVIDER_REGISTRY))}"
        )
    return builder(settings)
