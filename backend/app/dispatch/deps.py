"""Dispatch dependency providers (Dependency Injection wiring)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.api.deps import SessionDep
from app.dispatch.rules import RuleEngine
from app.dispatch.services import DispatchService
from app.gis.deps import GeocodingServiceDep


def get_rule_engine(request: Request) -> RuleEngine:
    """Return the process-wide RuleEngine from app state."""
    return request.app.state.rule_engine


RuleEngineDep = Annotated[RuleEngine, Depends(get_rule_engine)]


def get_dispatch_service(
    session: SessionDep,
    rule_engine: RuleEngineDep,
    geocoding: GeocodingServiceDep,
) -> DispatchService:
    return DispatchService(session, rule_engine, geocoding=geocoding)


DispatchServiceDep = Annotated[DispatchService, Depends(get_dispatch_service)]
