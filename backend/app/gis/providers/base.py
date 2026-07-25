"""Geocoding provider abstraction.

``GeoProvider`` is the single seam between the GIS core and any external
geocoding backend (Nominatim, Photon, Pelias, ArcGIS, and later Google / Yandex).
Every service depends on this interface — never on a concrete provider — so a
backend can be swapped purely through configuration (Dependency Inversion).

The DTOs below are provider-agnostic: each concrete provider maps its own
response shape onto them, so the rest of the system sees one consistent model.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GeoAccuracy(str, Enum):
    """Coarse confidence/precision of a geocoding result."""

    ROOFTOP = "rooftop"          # exact building
    HOUSE = "house"              # house-number level
    STREET = "street"            # street/segment level
    LOCALITY = "locality"        # settlement/city level
    REGION = "region"            # region/state level
    COUNTRY = "country"          # country level
    UNKNOWN = "unknown"


@dataclass(slots=True)
class GeocodeQuery:
    """Input for a forward-geocoding request."""

    query: str
    limit: int = 5
    language: str | None = None
    country_codes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class GeocodeResult:
    """A single forward-geocoding candidate (Address → Coordinates)."""

    formatted_address: str
    latitude: float
    longitude: float
    accuracy: GeoAccuracy = GeoAccuracy.UNKNOWN
    source: str = ""
    normalized_address: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AddressComponents:
    """Structured address parts (Coordinates → Address)."""

    country: str | None = None
    country_code: str | None = None
    region: str | None = None
    district: str | None = None
    settlement: str | None = None
    street: str | None = None
    house_number: str | None = None
    postal_code: str | None = None
    formatted_address: str | None = None


@dataclass(slots=True)
class ReverseResult:
    """A reverse-geocoding result with structured components."""

    components: AddressComponents
    latitude: float
    longitude: float
    accuracy: GeoAccuracy = GeoAccuracy.UNKNOWN
    source: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


class GeoProviderError(RuntimeError):
    """Raised when a provider fails to fulfil a request (network, HTTP, parse)."""


class GeoProvider(ABC):
    """Abstract geocoding backend.

    Concrete providers are stateless with respect to a request and receive their
    configuration (endpoint, credentials, timeout) via the constructor.
    """

    #: Stable identifier recorded on results and in the geocoding log.
    name: str = "base"

    @abstractmethod
    async def geocode(self, query: GeocodeQuery) -> list[GeocodeResult]:
        """Resolve a free-text address into ranked coordinate candidates."""
        raise NotImplementedError

    @abstractmethod
    async def reverse(
        self, latitude: float, longitude: float, *, language: str | None = None
    ) -> ReverseResult | None:
        """Resolve coordinates into a structured address."""
        raise NotImplementedError

    async def aclose(self) -> None:
        """Release any resources (HTTP clients). Default is a no-op."""
        return None
