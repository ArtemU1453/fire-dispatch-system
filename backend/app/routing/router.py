"""Aggregate router for the routing module."""

from __future__ import annotations

from fastapi import APIRouter

from app.routing.api import routing

routing_router = APIRouter()
routing_router.include_router(routing.router)
