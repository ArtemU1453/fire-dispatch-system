"""Geocoding REST endpoints.

Thin adapters over :class:`GeocodingService` / :class:`NormalizationService`.
All five endpoints required by Stage 3 live here:
``/geocode``, ``/reverse-geocode``, ``/coordinates``, ``/validate-address``,
``/normalize-address``.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.gis.deps import GeocodingServiceDep, NormalizationDep
from app.gis.schemas.geocoding import (
    AddressComponentsSchema,
    CoordinatesResponse,
    GeocodeResponse,
    GeocodeResultSchema,
    NormalizeResponse,
    ReverseGeocodeResponse,
    ValidateResponse,
)

router = APIRouter(tags=["gis-geocoding"])


def _to_result_schema(result) -> GeocodeResultSchema:
    return GeocodeResultSchema(
        formatted_address=result.formatted_address,
        normalized_address=result.normalized_address,
        latitude=result.latitude,
        longitude=result.longitude,
        accuracy=result.accuracy,
        source=result.source,
    )


@router.get("/geocode", response_model=GeocodeResponse, summary="Address → coordinates")
async def geocode(
    service: GeocodingServiceDep,
    q: str = Query(min_length=1, description="Free-text address to geocode."),
    limit: int = Query(default=5, ge=1, le=25),
    language: str | None = Query(default=None),
    country_codes: str | None = Query(
        default=None, description="Comma-separated ISO country codes, e.g. 'ru'."
    ),
) -> GeocodeResponse:
    codes = [c.strip() for c in country_codes.split(",")] if country_codes else None
    outcome = await service.geocode(
        q, limit=limit, language=language, country_codes=codes
    )
    return GeocodeResponse(
        query=outcome.query,
        normalized_address=outcome.normalized_address,
        provider=outcome.provider,
        from_cache=outcome.from_cache,
        success=outcome.success,
        error=outcome.error,
        count=len(outcome.results),
        results=[_to_result_schema(r) for r in outcome.results],
    )


@router.get(
    "/reverse-geocode",
    response_model=ReverseGeocodeResponse,
    summary="Coordinates → address",
)
async def reverse_geocode(
    service: GeocodingServiceDep,
    lat: float = Query(ge=-90.0, le=90.0),
    lon: float = Query(ge=-180.0, le=180.0),
    language: str | None = Query(default=None),
) -> ReverseGeocodeResponse:
    outcome = await service.reverse(lat, lon, language=language)
    result = outcome.result
    address = None
    if result is not None:
        c = result.components
        address = AddressComponentsSchema(
            country=c.country,
            country_code=c.country_code,
            region=c.region,
            district=c.district,
            settlement=c.settlement,
            street=c.street,
            house_number=c.house_number,
            postal_code=c.postal_code,
            formatted_address=c.formatted_address,
        )
    return ReverseGeocodeResponse(
        latitude=outcome.latitude,
        longitude=outcome.longitude,
        provider=outcome.provider,
        from_cache=outcome.from_cache,
        success=outcome.success,
        error=outcome.error,
        accuracy=result.accuracy if result else None,
        source=result.source if result else None,
        address=address,
    )


@router.get(
    "/coordinates",
    response_model=CoordinatesResponse,
    summary="Get coordinates of the best-matching address",
)
async def coordinates(
    service: GeocodingServiceDep,
    address: str = Query(min_length=1),
) -> CoordinatesResponse:
    outcome = await service.geocode(address, limit=1)
    best = outcome.results[0] if outcome.results else None
    return CoordinatesResponse(
        query=outcome.query,
        normalized_address=outcome.normalized_address,
        found=best is not None,
        latitude=best.latitude if best else None,
        longitude=best.longitude if best else None,
        accuracy=best.accuracy if best else None,
        source=best.source if best else None,
    )


@router.get(
    "/validate-address",
    response_model=ValidateResponse,
    summary="Validate that an address is geocodable",
)
async def validate_address(
    service: GeocodingServiceDep,
    address: str = Query(min_length=1),
) -> ValidateResponse:
    outcome = await service.validate(address)
    return ValidateResponse(
        query=outcome.query,
        normalized_address=outcome.normalized_address,
        is_valid=outcome.is_valid,
        best_match=(
            _to_result_schema(outcome.best_match) if outcome.best_match else None
        ),
    )


@router.get(
    "/normalize-address",
    response_model=NormalizeResponse,
    summary="Normalize an address to a canonical form",
)
async def normalize_address(
    normalization: NormalizationDep,
    address: str = Query(min_length=1),
) -> NormalizeResponse:
    result = normalization.normalize(address)
    return NormalizeResponse(
        raw=result.raw, normalized=result.normalized, canonical=result.canonical
    )
