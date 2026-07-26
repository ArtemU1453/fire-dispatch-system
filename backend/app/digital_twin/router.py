"""Aggregate router for the Digital Twin platform (Stage 18)."""

from __future__ import annotations

from fastapi import APIRouter

from app.digital_twin.api.digital_twin import router as _dt_router

digital_twin_router = APIRouter()
digital_twin_router.include_router(_dt_router)
