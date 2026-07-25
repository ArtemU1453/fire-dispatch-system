"""Routing dependency providers (Dependency Injection wiring).

The routing provider and route cache are process-wide (built once at startup and
shared via ``app.state``), mirroring the GIS provider wiring. Services are
per-request and cheap to construct.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.routing.interfaces.routing_provider import RoutingProvider
from app.routing.repositories.route_cache import RouteCache
from app.routing.services import ETAService, RouteService


def get_route_provider(request: Request) -> RoutingProvider:
    return request.app.state.route_provider


def get_route_cache(request: Request) -> RouteCache:
    return request.app.state.route_cache


RouteProviderDep = Annotated[RoutingProvider, Depends(get_route_provider)]
RouteCacheDep = Annotated[RouteCache, Depends(get_route_cache)]


def get_route_service(
    provider: RouteProviderDep, cache: RouteCacheDep
) -> RouteService:
    return RouteService(provider, cache=cache)


RouteServiceDep = Annotated[RouteService, Depends(get_route_service)]


def get_eta_service(request: Request, service: RouteServiceDep) -> ETAService:
    speed = getattr(request.app.state, "settings", None)
    average_speed = speed.ROUTING_AVERAGE_SPEED_KMH if speed is not None else 50.0
    return ETAService(service, average_speed_kmh=average_speed)


ETAServiceDep = Annotated[ETAService, Depends(get_eta_service)]
