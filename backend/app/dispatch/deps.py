"""Dispatch dependency providers (Dependency Injection wiring)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.deps import SessionDep
from app.dispatch.services import DispatchService
from app.gis.deps import GeocodingServiceDep


def get_dispatch_service(
    session: SessionDep,
    geocoding: GeocodingServiceDep,
) -> DispatchService:
    # The ETA provider is intentionally omitted at this stage (routing is a later
    # stage); the engine defaults to the null provider.
    return DispatchService(session, geocoding=geocoding)


DispatchServiceDep = Annotated[DispatchService, Depends(get_dispatch_service)]
