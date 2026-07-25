"""Aggregate router for the GIS module.

Included by the API v1 router. New GIS endpoint groups are added here without
changing the application factory (Open/Closed).
"""

from __future__ import annotations

from fastapi import APIRouter

from app.gis.api import geocoding, spatial

gis_router = APIRouter()
gis_router.include_router(geocoding.router)
gis_router.include_router(spatial.router)
