"""Resource-management dependency providers (Dependency Injection wiring)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.deps import SessionDep
from app.resources.services import ResourceManagementService


def get_resource_service(session: SessionDep) -> ResourceManagementService:
    return ResourceManagementService(session)


ResourceServiceDep = Annotated[
    ResourceManagementService, Depends(get_resource_service)
]
