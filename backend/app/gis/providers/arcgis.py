"""ArcGIS World Geocoding Service provider.

Uses the ArcGIS REST ``findAddressCandidates`` / ``reverseGeocode`` operations.
A token may be required depending on the deployment (``GIS_ARCGIS_TOKEN``).
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


class ArcGISProvider(HttpGeoProvider):
    """Geocoding via the ArcGIS World GeocodeServer."""

    name = "arcgis"

    def __init__(self, *args: Any, token: str | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._token = token

    def _with_token(self, params: dict[str, Any]) -> dict[str, Any]:
        if self._token:
            params["token"] = self._token
        return params

    async def geocode(self, query: GeocodeQuery) -> list[GeocodeResult]:
        params: dict[str, Any] = {
            "singleLine": query.query,
            "f": "json",
            "maxLocations": query.limit,
            "outFields": "*",
        }
        if query.country_codes:
            params["countryCode"] = ",".join(c.upper() for c in query.country_codes)
        data = await self._get_json("/findAddressCandidates", self._with_token(params))
        results: list[GeocodeResult] = []
        for cand in (data or {}).get("candidates", []):
            loc = cand.get("location", {})
            results.append(
                GeocodeResult(
                    formatted_address=cand.get("address", ""),
                    latitude=float(loc.get("y")),
                    longitude=float(loc.get("x")),
                    accuracy=self._accuracy(cand.get("score")),
                    source=self.name,
                    raw=cand,
                )
            )
        return results

    async def reverse(
        self, latitude: float, longitude: float, *, language: str | None = None
    ) -> ReverseResult | None:
        params: dict[str, Any] = {
            "location": f"{longitude},{latitude}",
            "f": "json",
        }
        data = await self._get_json("/reverseGeocode", self._with_token(params))
        if not data or "error" in data or "address" not in data:
            return None
        address = data["address"]
        loc = data.get("location", {})
        return ReverseResult(
            components=AddressComponents(
                country=address.get("CntryName"),
                country_code=(address.get("CountryCode") or "").lower() or None,
                region=address.get("Region"),
                district=address.get("Subregion") or address.get("MetroArea"),
                settlement=address.get("City"),
                street=address.get("Address"),
                house_number=None,
                postal_code=address.get("Postal"),
                formatted_address=address.get("LongLabel") or address.get("Match_addr"),
            ),
            latitude=float(loc.get("y", latitude)),
            longitude=float(loc.get("x", longitude)),
            accuracy=(
                GeoAccuracy.HOUSE if address.get("Address") else GeoAccuracy.LOCALITY
            ),
            source=self.name,
            raw=data,
        )

    @staticmethod
    def _accuracy(score: float | None) -> GeoAccuracy:
        if score is None:
            return GeoAccuracy.UNKNOWN
        if score >= 98:
            return GeoAccuracy.HOUSE
        if score >= 90:
            return GeoAccuracy.STREET
        if score >= 75:
            return GeoAccuracy.LOCALITY
        return GeoAccuracy.REGION
