"""Routing configuration (policy — provider choice, speeds, cache)."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings


@dataclass(frozen=True, slots=True)
class RoutingConfig:
    """Resolved routing settings the module operates on."""

    provider: str = "haversine"
    osrm_url: str | None = None
    http_timeout: float = 8.0
    average_speed_kmh: float = 50.0
    road_factor: float = 1.3
    enable_fallback: bool = True
    cache_backend: str = "memory"
    cache_ttl_seconds: int = 120
    cache_max_entries: int = 2000

    @classmethod
    def from_settings(cls, settings: Settings) -> RoutingConfig:
        return cls(
            provider=settings.ROUTING_PROVIDER,
            osrm_url=settings.ROUTING_OSRM_URL,
            http_timeout=settings.ROUTING_HTTP_TIMEOUT,
            average_speed_kmh=settings.ROUTING_AVERAGE_SPEED_KMH,
            road_factor=settings.ROUTING_ROAD_FACTOR,
            enable_fallback=settings.ROUTING_ENABLE_FALLBACK,
            cache_backend=settings.ROUTING_CACHE_BACKEND,
            cache_ttl_seconds=settings.ROUTING_CACHE_TTL_SECONDS,
            cache_max_entries=settings.ROUTING_CACHE_MAX_ENTRIES,
        )
