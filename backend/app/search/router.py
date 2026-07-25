"""Aggregate router for the search module."""

from __future__ import annotations

from fastapi import APIRouter

from app.search.api import resources

search_router = APIRouter()
search_router.include_router(resources.router)
