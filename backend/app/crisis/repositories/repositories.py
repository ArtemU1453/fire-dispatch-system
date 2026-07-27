"""Concrete repositories for the Crisis Management Platform (Stage 20).

Thin subclasses of the shared :class:`SqlAlchemyRepository` — CRUD, filtering,
sorting, pagination and soft-delete come for free (DRY).
"""

from __future__ import annotations

from app.crisis.models.entities import (
    CommandAssignment,
    CrisisResponseLevel,
    EmergencyOperation,
    JournalEntry,
    OperationalHeadquarters,
    OperationalOrder,
    OperationalSector,
    OperationalTask,
    OperationalZone,
    PlanStage,
    ResourceGroup,
    ResourceGroupMember,
    ResourceMove,
    SituationReport,
)
from app.repositories.base import SqlAlchemyRepository


class ResponseLevelRepository(SqlAlchemyRepository[CrisisResponseLevel]):
    model = CrisisResponseLevel


class OperationRepository(SqlAlchemyRepository[EmergencyOperation]):
    model = EmergencyOperation


class HeadquartersRepository(SqlAlchemyRepository[OperationalHeadquarters]):
    model = OperationalHeadquarters


class CommandAssignmentRepository(SqlAlchemyRepository[CommandAssignment]):
    model = CommandAssignment


class SectorRepository(SqlAlchemyRepository[OperationalSector]):
    model = OperationalSector


class ZoneRepository(SqlAlchemyRepository[OperationalZone]):
    model = OperationalZone


class ResourceGroupRepository(SqlAlchemyRepository[ResourceGroup]):
    model = ResourceGroup


class ResourceGroupMemberRepository(SqlAlchemyRepository[ResourceGroupMember]):
    model = ResourceGroupMember


class ResourceMoveRepository(SqlAlchemyRepository[ResourceMove]):
    model = ResourceMove


class PlanStageRepository(SqlAlchemyRepository[PlanStage]):
    model = PlanStage


class TaskRepository(SqlAlchemyRepository[OperationalTask]):
    model = OperationalTask


class SituationReportRepository(SqlAlchemyRepository[SituationReport]):
    model = SituationReport


class OperationalOrderRepository(SqlAlchemyRepository[OperationalOrder]):
    model = OperationalOrder


class JournalRepository(SqlAlchemyRepository[JournalEntry]):
    model = JournalEntry
