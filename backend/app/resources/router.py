"""Aggregate router for the resource-management module."""

from __future__ import annotations

from fastapi import APIRouter

from app.resources.api import resources

resources_router = APIRouter()
resources_router.include_router(resources.router)
