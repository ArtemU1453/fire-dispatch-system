"""Aggregate router for the rules module."""

from __future__ import annotations

from fastapi import APIRouter

from app.rules.api import rules

rules_router = APIRouter()
rules_router.include_router(rules.router)
