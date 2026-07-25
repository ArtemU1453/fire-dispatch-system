"""Photon (Komoot, OpenStreetMap-based) geocoding provider.

Photon returns GeoJSON; components live in feature ``properties``. Works against
the public endpoint or a self-hosted instance (``GIS_PHOTON_URL``).
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


class PhotonProvider(HttpGeoProvider):
    """Geocoding via the Photon REST API (GeoJSON responses)."""

    name = "photon"

    async def geocode(self, query: GeocodeQuery) -> list[GeocodeResult]:
        params: dict[str, Any] = {"q": query.query, "limit": query.limit}
        if query.language:
            params["lang"] = query.language
        data = await self._get_json("/api", params)
        results: list[GeocodeResult] = []
        for feature in (data or {}).get("features", []):
            lon, lat = feature["geometry"]["coordinates"]
            props = feature.get("properties", {})
            results.append(
                GeocodeResult(
                    formatted_address=self._format(props),
                    latitude=float(lat),
                    longitude=float(lon),
                    accuracy=self._accuracy(props),
                    source=self.name,
                    raw=feature,
                )
            )
        return results

    async def reverse(
        self, latitude: float, longitude: float, *, language: str | None = None
    ) -> ReverseResult | None:
        params: dict[str, Any] = {"lat": latitude, "lon": longitude}
        if language:
            params["lang"] = language
        data = await self._get_json("/reverse", params)
        features = (data or {}).get("features", [])
        if not features:
            return None
        feature = features[0]
        lon, lat = feature["geometry"]["coordinates"]
        props = feature.get("properties", {})
        return ReverseResult(
            components=self._components(props),
            latitude=float(lat),
            longitude=float(lon),
            accuracy=self._accuracy(props),
            source=self.name,
            raw=feature,
        )

    @classmethod
    def _components(cls, props: dict[str, Any]) -> AddressComponents:
        return AddressComponents(
            country=props.get("country"),
            country_code=props.get("countrycode"),
            region=props.get("state"),
            district=props.get("county") or props.get("district"),
            settlement=props.get("city") or props.get("town") or props.get("village"),
            street=props.get("street"),
            house_number=props.get("housenumber"),
            postal_code=props.get("postcode"),
            formatted_address=cls._format(props),
        )

    @staticmethod
    def _format(props: dict[str, Any]) -> str:
        parts = [
            props.get("name"),
            props.get("housenumber"),
            props.get("street"),
            props.get("city") or props.get("town") or props.get("village"),
            props.get("state"),
            props.get("country"),
        ]
        return ", ".join(p for p in parts if p)

    @staticmethod
    def _accuracy(props: dict[str, Any]) -> GeoAccuracy:
        if props.get("housenumber"):
            return GeoAccuracy.HOUSE
        if props.get("street"):
            return GeoAccuracy.STREET
        if props.get("city") or props.get("town") or props.get("village"):
            return GeoAccuracy.LOCALITY
        if props.get("state"):
            return GeoAccuracy.REGION
        if props.get("country"):
            return GeoAccuracy.COUNTRY
        return GeoAccuracy.UNKNOWN
