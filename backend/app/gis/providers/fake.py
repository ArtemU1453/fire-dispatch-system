"""Deterministic in-memory geocoding provider.

Used for local development and hermetic tests: it never touches the network and
returns predictable results from a small in-memory gazetteer, plus a deterministic
pseudo-coordinate fallback so any query resolves. Because it implements
``GeoProvider`` exactly like the real backends, services can be tested end-to-end
without mocking HTTP.
"""

from __future__ import annotations

import hashlib

from app.gis.providers.base import (
    AddressComponents,
    GeoAccuracy,
    GeocodeQuery,
    GeocodeResult,
    GeoProvider,
    ReverseResult,
)

# A tiny built-in gazetteer keyed by a normalized substring.
_GAZETTEER: dict[str, tuple[float, float, str]] = {
    "красная площадь": (55.753930, 37.620795, "Красная площадь, Москва, Россия"),
    "ленина": (55.751244, 37.618423, "улица Ленина, Москва, Россия"),
    "дворцовая площадь": (
        59.939099,
        30.315877,
        "Дворцовая площадь, Санкт-Петербург, Россия",
    ),
}


def _pseudo_coord(seed: str) -> tuple[float, float]:
    """Derive a stable lat/lon in a plausible range from a string."""
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    lat = 41.0 + (int.from_bytes(digest[:4], "big") % 3000) / 100.0  # 41..71
    lon = 20.0 + (int.from_bytes(digest[4:8], "big") % 16000) / 100.0  # 20..180
    return round(lat, 6), round(lon, 6)


class FakeGeoProvider(GeoProvider):
    """Offline, deterministic provider."""

    name = "fake"

    async def geocode(self, query: GeocodeQuery) -> list[GeocodeResult]:
        key = query.query.strip().lower()
        for needle, (lat, lon, formatted) in _GAZETTEER.items():
            if needle in key:
                return [
                    GeocodeResult(
                        formatted_address=formatted,
                        latitude=lat,
                        longitude=lon,
                        accuracy=GeoAccuracy.HOUSE,
                        source=self.name,
                        raw={"matched": needle},
                    )
                ]
        lat, lon = _pseudo_coord(key)
        return [
            GeocodeResult(
                formatted_address=query.query,
                latitude=lat,
                longitude=lon,
                accuracy=GeoAccuracy.LOCALITY,
                source=self.name,
                raw={"synthetic": True},
            )
        ]

    async def reverse(
        self, latitude: float, longitude: float, *, language: str | None = None
    ) -> ReverseResult | None:
        return ReverseResult(
            components=AddressComponents(
                country="Россия",
                country_code="ru",
                region="Москва",
                settlement="Москва",
                street="улица Ленина",
                house_number="1",
                formatted_address="улица Ленина, 1, Москва, Россия",
            ),
            latitude=latitude,
            longitude=longitude,
            accuracy=GeoAccuracy.HOUSE,
            source=self.name,
            raw={"synthetic": True},
        )
