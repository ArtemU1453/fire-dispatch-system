"""Dependency wiring for the Crisis Management API (Stage 20)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header

from app.api.deps import SessionDep
from app.crisis.services.board import ReportService, SituationBoardService
from app.crisis.services.journal import JournalService
from app.crisis.services.operations import OperationService
from app.crisis.services.plan import PlanService
from app.crisis.services.resources import ResourceGroupService
from app.crisis.services.sectors import SectorService


def get_operation_service(session: SessionDep) -> OperationService:
    return OperationService(session)


def get_sector_service(session: SessionDep) -> SectorService:
    return SectorService(session)


def get_resource_service(session: SessionDep) -> ResourceGroupService:
    return ResourceGroupService(session)


def get_plan_service(session: SessionDep) -> PlanService:
    return PlanService(session)


def get_report_service(session: SessionDep) -> ReportService:
    return ReportService(session)


def get_board_service(session: SessionDep) -> SituationBoardService:
    return SituationBoardService(session)


def get_journal_service(session: SessionDep) -> JournalService:
    return JournalService(session)


def get_actor(
    x_user_ref: Annotated[str | None, Header()] = None,
) -> str | None:
    """The acting user's display reference for journalling (optional header)."""
    return x_user_ref


def get_user_id(
    x_user_id: Annotated[str | None, Header()] = None,
) -> UUID | None:
    """The authenticated user id for RBAC (optional; open when absent)."""
    if not x_user_id:
        return None
    try:
        return UUID(x_user_id)
    except ValueError:
        return None


OperationServiceDep = Annotated[OperationService, Depends(get_operation_service)]
SectorServiceDep = Annotated[SectorService, Depends(get_sector_service)]
ResourceServiceDep = Annotated[ResourceGroupService, Depends(get_resource_service)]
PlanServiceDep = Annotated[PlanService, Depends(get_plan_service)]
ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]
BoardServiceDep = Annotated[SituationBoardService, Depends(get_board_service)]
JournalServiceDep = Annotated[JournalService, Depends(get_journal_service)]
ActorDep = Annotated["str | None", Depends(get_actor)]
UserIdDep = Annotated["UUID | None", Depends(get_user_id)]
