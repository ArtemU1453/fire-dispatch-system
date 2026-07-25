"""Pelias (e.g. geocode.earth) geocoding provider.

Pelias returns GeoJSON with a normalized ``properties`` block including a
``confidence`` score. An API key may be required for hosted instances
(``GIS_PELIAS_API_KEY``).
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

# Pelias "layer" → accuracy mapping.
_LAYER_ACCURACY = {
    "address": GeoAccuracy.HOUSE,
    "street": GeoAccuracy.STREET,
    "locality": GeoAccuracy.LOCALITY,
    "localadmin": GeoAccuracy.LOCALITY,
    "county": GeoAccuracy.REGION,
    "region": GeoAccuracy.REGION,
    "country": GeoAccuracy.COUNTRY,
}


class PeliasProvider(HttpGeoProvider):
    """Geocoding via the Pelias REST API (GeoJSON responses)."""

    name = "pelias"

    def __init__(self, *args: Any, api_key: str | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._api_key = api_key

    def _with_key(self, params: dict[str, Any]) -> dict[str, Any]:
        if self._api_key:
            params["api_key"] = self._api_key
        return params

    async def geocode(self, query: GeocodeQuery) -> list[GeocodeResult]:
        params: dict[str, Any] = {"text": query.query, "size": query.limit}
        if query.language:
            params["lang"] = query.language
        if query.country_codes:
            params["boundary.country"] = ",".join(
                c.upper() for c in query.country_codes
            )
        data = await self._get_json("/search", self._with_key(params))
        results: list[GeocodeResult] = []
        for feature in (data or {}).get("features", []):
            lon, lat = feature["geometry"]["coordinates"]
            props = feature.get("properties", {})
            results.append(
                GeocodeResult(
                    formatted_address=props.get("label", ""),
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
        params: dict[str, Any] = {"point.lat": latitude, "point.lon": longitude}
        if language:
            params["lang"] = language
        data = await self._get_json("/reverse", self._with_key(params))
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

    @staticmethod
    def _components(props: dict[str, Any]) -> AddressComponents:
        return AddressComponents(
            country=props.get("country"),
            country_code=(props.get("country_a") or "").lower() or None,
            region=props.get("region"),
            district=props.get("county"),
            settlement=props.get("locality") or props.get("localadmin"),
            street=props.get("street"),
            house_number=props.get("housenumber"),
            postal_code=props.get("postalcode"),
            formatted_address=props.get("label"),
        )

    @staticmethod
    def _accuracy(props: dict[str, Any]) -> GeoAccuracy:
        return _LAYER_ACCURACY.get(props.get("layer", ""), GeoAccuracy.UNKNOWN)
