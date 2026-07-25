"""Nominatim (OpenStreetMap) geocoding provider.

Default provider. Works against the public endpoint or a self-hosted instance
(configure ``GIS_NOMINATIM_URL``). Respect the OSM usage policy when using the
public server (meaningful User-Agent, low request rate).
"""

from __future__ import annotations

from typing import Any

from app.gis.providers.base import (
    AddressComponents,
    GeoAccuracy,
    GeocodeQuery,
    GeocodeResult,
    ReverseResult,
)
from app.gis.providers.http import HttpGeoProvider


class NominatimProvider(HttpGeoProvider):
    """Geocoding via the Nominatim REST API."""

    name = "nominatim"

    async def geocode(self, query: GeocodeQuery) -> list[GeocodeResult]:
        params: dict[str, Any] = {
            "q": query.query,
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": query.limit,
        }
        if query.language:
            params["accept-language"] = query.language
        if query.country_codes:
            params["countrycodes"] = ",".join(query.country_codes)

        data = await self._get_json("/search", params)
        results: list[GeocodeResult] = []
        for item in data or []:
            results.append(
                GeocodeResult(
                    formatted_address=item.get("display_name", ""),
                    latitude=float(item["lat"]),
                    longitude=float(item["lon"]),
                    accuracy=self._accuracy(item.get("address", {})),
                    source=self.name,
                    raw=item,
                )
            )
        return results

    async def reverse(
        self, latitude: float, longitude: float, *, language: str | None = None
    ) -> ReverseResult | None:
        params: dict[str, Any] = {
            "lat": latitude,
            "lon": longitude,
            "format": "jsonv2",
            "addressdetails": 1,
        }
        if language:
            params["accept-language"] = language

        data = await self._get_json("/reverse", params)
        if not data or "error" in data:
            return None
        address = data.get("address", {})
        return ReverseResult(
            components=self._components(address, data.get("display_name")),
            latitude=float(data.get("lat", latitude)),
            longitude=float(data.get("lon", longitude)),
            accuracy=self._accuracy(address),
            source=self.name,
            raw=data,
        )

    @staticmethod
    def _components(
        address: dict[str, Any], display_name: str | None
    ) -> AddressComponents:
        return AddressComponents(
            country=address.get("country"),
            country_code=address.get("country_code"),
            region=address.get("state") or address.get("region"),
            district=address.get("county") or address.get("city_district"),
            settlement=(
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("municipality")
            ),
            street=address.get("road"),
            house_number=address.get("house_number"),
            postal_code=address.get("postcode"),
            formatted_address=display_name,
        )

    @staticmethod
    def _accuracy(address: dict[str, Any]) -> GeoAccuracy:
        if address.get("house_number"):
            return GeoAccuracy.HOUSE
        if address.get("road"):
            return GeoAccuracy.STREET
        if address.get("city") or address.get("town") or address.get("village"):
            return GeoAccuracy.LOCALITY
        if address.get("state") or address.get("region"):
            return GeoAccuracy.REGION
        if address.get("country"):
            return GeoAccuracy.COUNTRY
        return GeoAccuracy.UNKNOWN
