"""Schemas for the time-series history entities."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.schemas.common import ResponseBase, SchemaBase

# ------------------------------------------------------------ status history --


class StatusHistoryCreate(SchemaBase):
    resource_id: UUID
    from_status_id: UUID | None = None
    to_status_id: UUID
    changed_by_user_id: UUID | None = None
    reason: str | None = None


class StatusHistoryUpdate(SchemaBase):
    # History is append-only in practice; only the free-text reason is editable
    # (e.g. to correct a note). See docs/data-model.md.
    reason: str | None = None


class StatusHistoryResponse(ResponseBase):
    resource_id: UUID
    from_status_id: UUID | None = None
    to_status_id: UUID
    changed_at: datetime
    changed_by_user_id: UUID | None = None
    reason: str | None = None


# -------------------------------------------------------- coordinate history --


class CoordinateHistoryCreate(SchemaBase):
    resource_id: UUID
    latitude: float | None = None
    longitude: float | None = None
    speed_kmh: float | None = None
    heading_deg: float | None = None
    accuracy_m: float | None = None


class CoordinateHistoryUpdate(SchemaBase):
    # Append-only telemetry; only correctable accuracy metadata is exposed.
    accuracy_m: float | None = None


class CoordinateHistoryResponse(ResponseBase):
    resource_id: UUID
    latitude: float | None = None
    longitude: float | None = None
    recorded_at: datetime
    speed_kmh: float | None = None
    heading_deg: float | None = None
    accuracy_m: float | None = None
