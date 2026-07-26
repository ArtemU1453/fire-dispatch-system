"""Aggregate router for the simulation & training platform (Stage 17)."""

from __future__ import annotations

from fastapi import APIRouter

from app.simulator.api.simulator import router as _training_router

simulator_router = APIRouter()
simulator_router.include_router(_training_router)
