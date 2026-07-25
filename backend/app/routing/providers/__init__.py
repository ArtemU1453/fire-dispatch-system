"""Routing providers and the provider factory.

``create_provider`` builds the configured provider. The straight-line
``haversine`` estimator is always available; when OSRM is configured it is used
as the primary with the estimator as an automatic fallback (unless disabled), so
a routing outage degrades gracefully instead of failing.
"""

from __future__ import annotations

from app.routing.config import RoutingConfig
from app.routing.interfaces.routing_provider import RoutingProvider
from app.routing.providers.fallback import FallbackRoutingProvider
from app.routing.providers.haversine import HaversineRoutingProvider
from app.routing.providers.osrm import OSRMProvider

__all__ = [
    "FallbackRoutingProvider",
    "HaversineRoutingProvider",
    "OSRMProvider",
    "create_provider",
]


def create_provider(config: RoutingConfig) -> RoutingProvider:
    """Build the routing provider from configuration."""
    estimator = HaversineRoutingProvider(
        average_speed_kmh=config.average_speed_kmh,
        road_factor=config.road_factor,
        is_fallback=False,
    )
    if config.provider == "osrm" and config.osrm_url:
        osrm = OSRMProvider(config.osrm_url, timeout=config.http_timeout)
        if config.enable_fallback:
            # Fallback estimator is flagged so callers know the result is degraded.
            fallback = HaversineRoutingProvider(
                average_speed_kmh=config.average_speed_kmh,
                road_factor=config.road_factor,
                is_fallback=True,
            )
            return FallbackRoutingProvider([osrm, fallback])
        return osrm
    return estimator
