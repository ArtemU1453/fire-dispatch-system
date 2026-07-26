"""Pydantic schemas for the mobile REST API (Stage 19)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ------------------------------------------------------------------ common ---
class IncidentView(BaseModel):
    id: str
    category: str
    priority: str
    status: str
    address: str
    description: str
    lat: float | None
    lon: float | None
    created_at: str
    recommended_units: list[str] = Field(default_factory=list)
    assigned_unit_ids: list[str] = Field(default_factory=list)


class ResourceView(BaseModel):
    unit_id: str
    name: str
    category: str
    status: str
    busy: bool
    lat: float | None = None
    lon: float | None = None


class SummaryView(BaseModel):
    active_incidents: int
    available_units: int
    busy_units: int
    calls_today: int


class CriticalView(BaseModel):
    id: str
    type: str
    message: str
    created_at: str
    incident_id: str | None = None
    severity: str = "critical"


# --------------------------------------------------------------- commander ---
class DashboardResponse(BaseModel):
    summary: SummaryView
    active_incidents: list[IncidentView]
    resource_load: list[ResourceView]
    critical: list[CriticalView]


class MapResponse(BaseModel):
    incidents: list[IncidentView]
    units: list[ResourceView]


class NoteRequest(BaseModel):
    author: str = "commander"
    text: str
    incident_id: str | None = None
    kind: str = "note"          # note | comment | confirmation


class NoteView(BaseModel):
    id: str
    author: str
    text: str
    created_at: str
    incident_id: str | None = None
    kind: str = "note"


# --------------------------------------------------------------- responder ---
class RoutePointView(BaseModel):
    lat: float
    lon: float


class RouteResponse(BaseModel):
    points: list[RoutePointView]
    distance_km: float
    eta_seconds: float | None = None


class DispatchResponse(BaseModel):
    incident_id: str
    address: str
    description: str
    category: str
    priority: str
    recommended_composition: list[str]
    contact: str | None = None
    lat: float | None = None
    lon: float | None = None
    current_status: str


class StatusUpdateRequest(BaseModel):
    unit_id: str
    status: str


class StatusUpdateResponse(BaseModel):
    unit_id: str
    status: str


class MessageRequest(BaseModel):
    unit_id: str
    from_user: str = ""
    text: str
    incident_id: str | None = None


class MessageView(BaseModel):
    id: str
    from_user: str
    text: str
    created_at: str
    unit_id: str | None = None
    incident_id: str | None = None


# ---------------------------------------------------------------- push/sync ---
class DeviceRegisterRequest(BaseModel):
    token: str
    user_id: str
    platform: str = "unknown"
    app: str = "responder"


class DeviceRegisterResponse(BaseModel):
    registered: bool
    token: str


class SyncOperationRequest(BaseModel):
    op_id: str
    type: str
    payload: dict[str, Any] = Field(default_factory=dict)


class SyncBatchRequest(BaseModel):
    operations: list[SyncOperationRequest]


class SyncResultView(BaseModel):
    op_id: str
    applied: bool
    duplicate: bool = False
    error: str | None = None
    result: dict[str, Any] | None = None


class SyncBatchResponse(BaseModel):
    results: list[SyncResultView]
