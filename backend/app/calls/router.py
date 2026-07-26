"""Aggregate router for the calls module."""

from __future__ import annotations

from fastapi import APIRouter

from app.calls.api import calls

calls_router = APIRouter()
calls_router.include_router(calls.router)
