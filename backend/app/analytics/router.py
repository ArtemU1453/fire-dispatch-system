"""Aggregate router for the analytics module."""

from __future__ import annotations

from fastapi import APIRouter

from app.analytics.api import analytics

analytics_router = APIRouter()
analytics_router.include_router(analytics.router)
