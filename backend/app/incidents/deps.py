"""Incident dependency providers (Dependency Injection wiring)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.deps import SessionDep
from app.incidents.services import IncidentService


def get_incident_service(session: SessionDep) -> IncidentService:
    return IncidentService(session)


IncidentServiceDep = Annotated[IncidentService, Depends(get_incident_service)]
