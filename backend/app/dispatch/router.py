"""Aggregate router for the dispatch module."""

from __future__ import annotations

from fastapi import APIRouter

from app.dispatch.api import dispatch

dispatch_router = APIRouter()
dispatch_router.include_router(dispatch.router)
