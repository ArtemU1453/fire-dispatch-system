"""System settings endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.admin.deps import SettingsServiceDep
from app.admin.models.enums import SettingCategory
from app.admin.schemas.admin import (
    SettingCreate,
    SettingHistoryResponse,
    SettingResponse,
    SettingUpdate,
)
from app.admin.utils.mapping import (
    setting_history_to_response,
    setting_to_response,
)

router = APIRouter(tags=["admin: settings"])


@router.get(
    "/settings", response_model=list[SettingResponse], summary="List settings"
)
async def list_settings(
    service: SettingsServiceDep,
    category: SettingCategory | None = Query(default=None),
) -> list[SettingResponse]:
    items = await service.list_settings(category=category)
    return [setting_to_response(s) for s in items]


@router.post(
    "/settings", response_model=SettingResponse,
    status_code=status.HTTP_201_CREATED, summary="Create a setting",
)
async def create_setting(
    service: SettingsServiceDep, data: SettingCreate
) -> SettingResponse:
    return setting_to_response(await service.create_setting(data))


@router.get(
    "/settings/{key}", response_model=SettingResponse, summary="Get a setting"
)
async def get_setting(service: SettingsServiceDep, key: str) -> SettingResponse:
    return setting_to_response(await service.get_setting(key))


@router.patch(
    "/settings/{key}", response_model=SettingResponse, summary="Update a setting"
)
async def update_setting(
    service: SettingsServiceDep, key: str, data: SettingUpdate
) -> SettingResponse:
    return setting_to_response(await service.update_setting(key, data))


@router.get(
    "/settings/{key}/history", response_model=list[SettingHistoryResponse],
    summary="A setting's change history",
)
async def setting_history(
    service: SettingsServiceDep, key: str
) -> list[SettingHistoryResponse]:
    rows = await service.history(key)
    return [setting_history_to_response(h) for h in rows]
