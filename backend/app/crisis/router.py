"""Aggregate router for the Crisis Management Platform (Stage 20)."""

from __future__ import annotations

from fastapi import APIRouter

from app.crisis.api.crisis import router as _crisis_router

crisis_router = APIRouter()
crisis_router.include_router(_crisis_router)
