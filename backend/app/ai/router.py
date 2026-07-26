"""Aggregate router for the AI platform module."""

from __future__ import annotations

from fastapi import APIRouter

from app.ai.api import ai

ai_router = APIRouter()
ai_router.include_router(ai.router)
