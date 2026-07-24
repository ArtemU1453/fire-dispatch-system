"""API dependency providers (Dependency Injection wiring).

Thin factory functions that assemble services from lower-level dependencies
(settings, database session). Endpoints declare what they need via ``Depends``
and never construct collaborators themselves, keeping the API layer decoupled
from concrete implementations.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.database import get_db_session
from app.services.health import HealthService

# Reusable typed dependency aliases.
SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def get_health_service(
    session: SessionDep,
    settings: SettingsDep,
) -> HealthService:
    """Provide a configured :class:`HealthService`."""
    return HealthService(session=session, settings=settings)


HealthServiceDep = Annotated[HealthService, Depends(get_health_service)]
