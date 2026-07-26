"""Integration management endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from app.admin.deps import IntegrationServiceDep
from app.admin.schemas.admin import (
    IntegrationCreate,
    IntegrationHealthResponse,
    IntegrationProviderResponse,
    IntegrationResponse,
    IntegrationUpdate,
)
from app.admin.utils.mapping import (
    health_to_response,
    integration_provider_to_response,
    integration_to_response,
)

router = APIRouter(tags=["admin: integrations"])


@router.get(
    "/integrations", response_model=list[IntegrationResponse],
    summary="List integrations",
)
async def list_integrations(
    service: IntegrationServiceDep,
) -> list[IntegrationResponse]:
    items = await service.list_integrations()
    return [
        integration_to_response(i, latest_health=service.latest_health(i))
        for i in items
    ]


@router.post(
    "/integrations", response_model=IntegrationResponse,
    status_code=status.HTTP_201_CREATED, summary="Create an integration",
)
async def create_integration(
    service: IntegrationServiceDep, data: IntegrationCreate
) -> IntegrationResponse:
    integration = await service.create_integration(data)
    return integration_to_response(
        integration, latest_health=service.latest_health(integration)
    )


@router.get(
    "/integrations/{integration_id}", response_model=IntegrationResponse,
    summary="Get an integration",
)
async def get_integration(
    service: IntegrationServiceDep, integration_id: UUID
) -> IntegrationResponse:
    integration = await service.get_integration(integration_id)
    return integration_to_response(
        integration, latest_health=service.latest_health(integration)
    )


@router.patch(
    "/integrations/{integration_id}", response_model=IntegrationResponse,
    summary="Update an integration",
)
async def update_integration(
    service: IntegrationServiceDep,
    integration_id: UUID,
    data: IntegrationUpdate,
) -> IntegrationResponse:
    integration = await service.update_integration(integration_id, data)
    return integration_to_response(
        integration, latest_health=service.latest_health(integration)
    )


@router.post(
    "/integrations/{integration_id}/health",
    response_model=IntegrationHealthResponse, summary="Run a health check",
)
async def integration_health(
    service: IntegrationServiceDep, integration_id: UUID
) -> IntegrationHealthResponse:
    check = await service.health_check(integration_id)
    return health_to_response(check)


@router.get(
    "/integration-providers",
    response_model=list[IntegrationProviderResponse],
    summary="List integration providers",
)
async def list_providers(
    service: IntegrationServiceDep,
) -> list[IntegrationProviderResponse]:
    providers = await service.list_providers()
    return [integration_provider_to_response(p) for p in providers]
