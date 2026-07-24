"""Aggregate router for API version 1.

New endpoint modules are included here as the domain grows. Keeping a single
aggregation point means the app factory never changes when routes are added
(Open/Closed Principle).
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import health

api_router = APIRouter()
api_router.include_router(health.router)
