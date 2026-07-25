"""Aggregate router for the incidents module."""

from __future__ import annotations

from fastapi import APIRouter

from app.incidents.api import incidents

incidents_router = APIRouter()
incidents_router.include_router(incidents.router)
