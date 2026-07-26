"""Directory (catalog) management endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from app.admin.deps import DirectoryServiceDep
from app.admin.schemas.admin import (
    DirectoryInfo,
    DirectoryItemCreate,
    DirectoryItemResponse,
    DirectoryItemUpdate,
)
from app.admin.utils.mapping import directory_item_to_response

router = APIRouter(tags=["admin: directories"])


@router.get(
    "/directories", response_model=list[DirectoryInfo],
    summary="List editable directories",
)
async def list_directories(
    service: DirectoryServiceDep,
) -> list[DirectoryInfo]:
    return [
        DirectoryInfo(name=name, label=label, editable_fields=fields)
        for name, label, fields in service.directories()
    ]


@router.get(
    "/directories/{name}", response_model=list[DirectoryItemResponse],
    summary="List directory items",
)
async def list_directory_items(
    service: DirectoryServiceDep, name: str
) -> list[DirectoryItemResponse]:
    model = service.resolve(name)
    items = await service.list_items(name)
    return [directory_item_to_response(i, model) for i in items]


@router.post(
    "/directories/{name}", response_model=DirectoryItemResponse,
    status_code=status.HTTP_201_CREATED, summary="Create a directory item",
)
async def create_directory_item(
    service: DirectoryServiceDep, name: str, data: DirectoryItemCreate
) -> DirectoryItemResponse:
    model = service.resolve(name)
    item = await service.create_item(name, data)
    return directory_item_to_response(item, model)


@router.patch(
    "/directories/{name}/{item_id}", response_model=DirectoryItemResponse,
    summary="Update a directory item",
)
async def update_directory_item(
    service: DirectoryServiceDep,
    name: str,
    item_id: UUID,
    data: DirectoryItemUpdate,
) -> DirectoryItemResponse:
    model = service.resolve(name)
    item = await service.update_item(name, item_id, data)
    return directory_item_to_response(item, model)
