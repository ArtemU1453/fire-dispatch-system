"""Pydantic schemas for the Crisis Management Platform (Stage 20 §11)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

_ORM = ConfigDict(from_attributes=True)


# ------------------------------------------------------------- responses ----
class ResponseLevelResponse(BaseModel):
    model_config = _ORM
    id: UUID
    code: str
    name: str
    rank: int
    description: str | None = None


class OperationResponse(BaseModel):
    model_config = _ORM
    id: UUID
    name: str
    code: str
    status: str
    response_level_id: UUID | None = None
    incident_ref: str | None = None
    description: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime


class HeadquartersResponse(BaseModel):
    model_config = _ORM
    id: UUID
    operation_id: UUID
    name: str
    notes: str | None = None


class CommanderResponse(BaseModel):
    model_config = _ORM
    id: UUID
    headquarters_id: UUID
    role: str
    user_ref: str
    display_name: str | None = None
    responsibilities: str | None = None


class SectorResponse(BaseModel):
    model_config = _ORM
    id: UUID
    operation_id: UUID
    name: str
    leader_ref: str | None = None
    status: str
    situation: str | None = None
    position: int
    center_lat: float | None = None
    center_lon: float | None = None


class ZoneResponse(BaseModel):
    model_config = _ORM
    id: UUID
    operation_id: UUID
    sector_id: UUID | None = None
    label: str
    kind: str
    center_lat: float | None = None
    center_lon: float | None = None
    radius_m: float | None = None


class ResourceGroupResponse(BaseModel):
    model_config = _ORM
    id: UUID
    operation_id: UUID
    sector_id: UUID | None = None
    name: str
    purpose: str | None = None


class ResourceMemberResponse(BaseModel):
    model_config = _ORM
    id: UUID
    group_id: UUID
    kind: str
    ref: str
    label: str | None = None


class ResourceMoveResponse(BaseModel):
    model_config = _ORM
    id: UUID
    group_id: UUID
    from_sector_id: UUID | None = None
    to_sector_id: UUID | None = None
    note: str | None = None
    created_at: datetime


class PlanStageResponse(BaseModel):
    model_config = _ORM
    id: UUID
    operation_id: UUID
    name: str
    position: int
    status: str


class TaskResponse(BaseModel):
    model_config = _ORM
    id: UUID
    operation_id: UUID
    stage_id: UUID | None = None
    sector_id: UUID | None = None
    title: str
    description: str | None = None
    assignee_ref: str | None = None
    due_at: datetime | None = None
    status: str
    position: int


class SituationReportResponse(BaseModel):
    model_config = _ORM
    id: UUID
    operation_id: UUID
    author_ref: str | None = None
    summary: str
    data: dict[str, Any] | None = None
    created_at: datetime


class OrderResponse(BaseModel):
    model_config = _ORM
    id: UUID
    operation_id: UUID
    number: str
    text: str
    issued_by_ref: str | None = None
    created_at: datetime


class JournalEntryResponse(BaseModel):
    model_config = _ORM
    id: UUID
    operation_id: UUID
    kind: str
    actor_ref: str | None = None
    message: str
    rationale: str | None = None
    payload: dict[str, Any] | None = None
    created_at: datetime


# DecisionResponse is a journal entry of kind "decision" (§11).
DecisionResponse = JournalEntryResponse


class SituationBoardResponse(BaseModel):
    operation_id: UUID
    sectors: list[SectorResponse]
    zones: list[ZoneResponse]
    resource_groups: list[ResourceGroupResponse]
    critical_events: list[JournalEntryResponse]
    latest_report: SituationReportResponse | None = None


# -------------------------------------------------------------- requests ----
class OperationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=64)
    response_level_code: str | None = None
    incident_ref: str | None = None
    description: str | None = None
    started_at: datetime | None = None


class OperationUpdate(BaseModel):
    name: str | None = None
    status: str | None = None
    description: str | None = None
    response_level_code: str | None = None
    started_at: datetime | None = None


class CommandAssignCreate(BaseModel):
    role: str
    user_ref: str
    display_name: str | None = None
    responsibilities: str | None = None


class DecisionCreate(BaseModel):
    decision: str = Field(min_length=1)
    rationale: str | None = None


class SectorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    leader_ref: str | None = None
    center_lat: float | None = None
    center_lon: float | None = None


class SectorUpdate(BaseModel):
    name: str | None = None
    leader_ref: str | None = None
    status: str | None = None
    situation: str | None = None
    center_lat: float | None = None
    center_lon: float | None = None


class ZoneCreate(BaseModel):
    label: str = Field(min_length=1, max_length=255)
    kind: str = "hot"
    sector_id: UUID | None = None
    center_lat: float | None = None
    center_lon: float | None = None
    radius_m: float | None = None


class ResourceGroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    purpose: str | None = None
    sector_id: UUID | None = None


class ResourceMemberCreate(BaseModel):
    kind: str
    ref: str
    label: str | None = None


class RelocateRequest(BaseModel):
    to_sector_id: UUID | None = None
    note: str | None = None


class StageCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    position: int = 0


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    stage_id: UUID | None = None
    sector_id: UUID | None = None
    assignee_ref: str | None = None
    due_at: datetime | None = None


class StatusUpdate(BaseModel):
    status: str


class ReportCreate(BaseModel):
    summary: str = Field(min_length=1)
    author_ref: str | None = None
    data: dict[str, Any] | None = None


class OrderCreate(BaseModel):
    number: str = Field(min_length=1, max_length=64)
    text: str = Field(min_length=1)
    issued_by_ref: str | None = None
