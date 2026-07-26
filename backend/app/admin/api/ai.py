"""AI administration endpoints and auth-method listing."""

from __future__ import annotations

from fastapi import APIRouter

from app.admin.deps import AIAdminServiceDep
from app.admin.schemas.admin import AISettingsResponse

router = APIRouter(tags=["admin: ai"])


@router.get(
    "/ai/providers", response_model=AISettingsResponse,
    summary="AI providers, state and parameters",
)
async def ai_overview(service: AIAdminServiceDep) -> AISettingsResponse:
    return await service.overview()
