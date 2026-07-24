"""Schemas for the health-check endpoint."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.schemas.common import SchemaBase


class HealthStatus(SchemaBase):
    """Response body for ``GET /health``."""

    status: Literal["ok", "degraded"] = Field(
        description="Overall service status."
    )
    app: str = Field(description="Application name.")
    version: str = Field(description="Application version.")
    environment: str = Field(description="Deployment environment.")
    database: Literal["up", "down"] = Field(
        description="Database connectivity status."
    )
