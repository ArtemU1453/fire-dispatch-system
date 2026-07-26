"""Aggregate router for the mobile platform (Stage 19)."""

from __future__ import annotations

from fastapi import APIRouter

from app.mobile.api.mobile import router as _mobile_router

mobile_router = APIRouter()
mobile_router.include_router(_mobile_router)
