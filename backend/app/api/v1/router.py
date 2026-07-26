"""Aggregate router for API version 1.

New endpoint modules are included here as the domain grows. Keeping a single
aggregation point means the app factory never changes when routes are added
(Open/Closed Principle).
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import health
from app.dispatch.router import dispatch_router
from app.gis.router import gis_router
from app.incidents.router import incidents_router
from app.resources.router import resources_router
from app.routing.router import routing_router
from app.rules.router import rules_router
from app.search.router import search_router

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(gis_router)
# Resource-management routes (incl. the literal /resources/status and
# /resources/history) are registered *before* the search router so they are not
# shadowed by the search module's dynamic /resources/{resource_id}.
api_router.include_router(resources_router)
api_router.include_router(search_router)
api_router.include_router(dispatch_router)
api_router.include_router(rules_router)
api_router.include_router(routing_router)
api_router.include_router(incidents_router)
