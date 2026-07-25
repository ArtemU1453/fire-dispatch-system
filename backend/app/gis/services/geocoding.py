"""Geocoding service — forward, reverse and validation.

Orchestrates the provider, cache, normalization and logging around every
request. Depends only on the :class:`GeoProvider` and :class:`GeoCache`
interfaces (Dependency Inversion), so backends swap via configuration.

Every request is recorded in ``gis_geocoding_logs`` with timing, provider,
source, success/error and cache-hit — persisted in its own short transaction so
the log survives regardless of the outcome of the surrounding request.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import Settings, get_settings
from app.core.logging import get_logger
from app.database.session import SessionFactory
from app.gis.cache.base import GeoCache
from app.gis.models import GeocodingLog
from app.gis.providers.base import (
    GeocodeQuery,
    GeocodeResult,
    GeoProvider,
    GeoProviderError,
    ReverseResult,
)
from app.gis.services.normalization import NormalizationService

logger = get_logger(__name__)


@dataclass(slots=True)
class GeocodeOutcome:
    """Result of a forward-geocoding request."""

    query: str
    normalized_address: str
    results: list[GeocodeResult] = field(default_factory=list)
    provider: str = ""
    from_cache: bool = False
    success: bool = True
    error: str | None = None


@dataclass(slots=True)
class ReverseOutcome:
    """Result of a reverse-geocoding request."""

    latitude: float
    longitude: float
    result: ReverseResult | None = None
    provider: str = ""
    from_cache: bool = False
    success: bool = True
    error: str | None = None


@dataclass(slots=True)
class ValidationOutcome:
    """Result of validating an address."""

    query: str
    normalized_address: str
    is_valid: bool
    best_match: GeocodeResult | None = None


class GeocodingService:
    """Forward / reverse geocoding and address validation."""

    def __init__(
        self,
        provider: GeoProvider,
        cache: GeoCache,
        *,
        normalization: NormalizationService | None = None,
        settings: Settings | None = None,
        log_session_factory: async_sessionmaker | None = None,
    ) -> None:
        self._provider = provider
        self._cache = cache
        self._normalization = normalization or NormalizationService()
        self._settings = settings or get_settings()
        self._log_session_factory = log_session_factory or SessionFactory

    # ------------------------------------------------------------- geocode ---
    async def geocode(
        self,
        query: str,
        *,
        limit: int = 5,
        language: str | None = None,
        country_codes: list[str] | None = None,
    ) -> GeocodeOutcome:
        language = language or self._settings.GIS_DEFAULT_LANGUAGE
        country_codes = country_codes or self._settings.GIS_DEFAULT_COUNTRY_CODES
        normalized = self._normalization.normalize(query)
        cache_key = (
            f"geocode:{self._provider.name}:{normalized.canonical}:{limit}:{language}"
        )

        cached = await self._cache.get(cache_key)
        if cached is not None:
            results = [GeocodeResult(**item) for item in cached]
            for r in results:
                r.normalized_address = normalized.normalized
            await self._write_log(
                "geocode", query, True, source=self._provider.name,
                result_count=len(results), from_cache=True, elapsed_ms=0.0,
            )
            return GeocodeOutcome(
                query=query,
                normalized_address=normalized.normalized,
                results=results,
                provider=self._provider.name,
                from_cache=True,
            )

        started = time.perf_counter()
        try:
            results = await self._provider.geocode(
                GeocodeQuery(
                    query=query,
                    limit=limit,
                    language=language,
                    country_codes=list(country_codes),
                )
            )
        except GeoProviderError as exc:
            elapsed = (time.perf_counter() - started) * 1000
            await self._write_log(
                "geocode", query, False, source=self._provider.name,
                error=str(exc), elapsed_ms=elapsed,
            )
            logger.warning("Geocoding failed: %s", exc)
            return GeocodeOutcome(
                query=query,
                normalized_address=normalized.normalized,
                provider=self._provider.name,
                success=False,
                error=str(exc),
            )

        elapsed = (time.perf_counter() - started) * 1000
        for r in results:
            r.normalized_address = normalized.normalized
        await self._cache.set(cache_key, [asdict(r) for r in results])
        await self._write_log(
            "geocode", query, True, source=self._provider.name,
            result_count=len(results), elapsed_ms=elapsed,
        )
        return GeocodeOutcome(
            query=query,
            normalized_address=normalized.normalized,
            results=results,
            provider=self._provider.name,
        )

    # ------------------------------------------------------------- reverse ---
    async def reverse(
        self, latitude: float, longitude: float, *, language: str | None = None
    ) -> ReverseOutcome:
        language = language or self._settings.GIS_DEFAULT_LANGUAGE
        cache_key = (
            f"reverse:{self._provider.name}:{latitude:.6f}:{longitude:.6f}:{language}"
        )

        cached = await self._cache.get(cache_key)
        if cached is not None:
            await self._write_log(
                "reverse", f"{latitude},{longitude}", True,
                source=self._provider.name, result_count=1, from_cache=True,
                latitude=latitude, longitude=longitude, elapsed_ms=0.0,
            )
            return ReverseOutcome(
                latitude=latitude, longitude=longitude,
                result=_reverse_from_cache(cached), provider=self._provider.name,
                from_cache=True,
            )

        started = time.perf_counter()
        try:
            result = await self._provider.reverse(
                latitude, longitude, language=language
            )
        except GeoProviderError as exc:
            elapsed = (time.perf_counter() - started) * 1000
            await self._write_log(
                "reverse", f"{latitude},{longitude}", False,
                source=self._provider.name, error=str(exc),
                latitude=latitude, longitude=longitude, elapsed_ms=elapsed,
            )
            logger.warning("Reverse geocoding failed: %s", exc)
            return ReverseOutcome(
                latitude=latitude, longitude=longitude,
                provider=self._provider.name, success=False, error=str(exc),
            )

        elapsed = (time.perf_counter() - started) * 1000
        if result is not None:
            await self._cache.set(cache_key, _reverse_to_cache(result))
        await self._write_log(
            "reverse", f"{latitude},{longitude}", result is not None,
            source=self._provider.name, result_count=1 if result else 0,
            latitude=latitude, longitude=longitude, elapsed_ms=elapsed,
        )
        return ReverseOutcome(
            latitude=latitude, longitude=longitude,
            result=result, provider=self._provider.name,
        )

    # ------------------------------------------------------------ validate ---
    async def validate(self, address: str) -> ValidationOutcome:
        outcome = await self.geocode(address, limit=1)
        best = outcome.results[0] if outcome.results else None
        return ValidationOutcome(
            query=address,
            normalized_address=outcome.normalized_address,
            is_valid=best is not None,
            best_match=best,
        )

    # ------------------------------------------------------------- logging ---
    async def _write_log(
        self,
        operation: str,
        query: str,
        success: bool,
        *,
        source: str,
        result_count: int = 0,
        error: str | None = None,
        from_cache: bool = False,
        latitude: float | None = None,
        longitude: float | None = None,
        elapsed_ms: float | None = None,
    ) -> None:
        """Persist a geocoding log row in its own transaction (durable)."""
        try:
            async with self._log_session_factory() as session:
                session.add(
                    GeocodingLog(
                        operation=operation,
                        provider=self._provider.name,
                        query=query[:1024],
                        success=success,
                        result_count=result_count,
                        response_time_ms=elapsed_ms,
                        source=source,
                        error=(error[:1024] if error else None),
                        latitude=latitude,
                        longitude=longitude,
                        from_cache=from_cache,
                    )
                )
                await session.commit()
        except Exception as exc:  # noqa: BLE001 - logging must never break the request
            logger.warning("Failed to write geocoding log: %s", exc)


def _reverse_to_cache(result: ReverseResult) -> dict:
    data = asdict(result)
    return data


def _reverse_from_cache(data: dict) -> ReverseResult:
    from app.gis.providers.base import AddressComponents, GeoAccuracy

    components = AddressComponents(**data["components"])
    return ReverseResult(
        components=components,
        latitude=data["latitude"],
        longitude=data["longitude"],
        accuracy=GeoAccuracy(data["accuracy"]),
        source=data["source"],
        raw=data.get("raw", {}),
    )
