"""Aggregate router for the observability module."""

from __future__ import annotations

from fastapi import APIRouter

from app.observability.api import observability

observability_router = APIRouter()
observability_router.include_router(observability.router)
