"""Application-level enums for the Crisis Management Platform (Stage 20).

These are **validation vocabularies** used by the service and schema layers. To
keep migrations simple and avoid native-enum drift, the ORM stores their
*values* as plain ``String`` columns; these classes constrain and document the
allowed values. Response *levels* are NOT here — they live in a configurable
reference table (``crisis_response_levels``) so they can change without code.
"""

from __future__ import annotations

from enum import Enum


class OperationStatus(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    STABILIZING = "stabilizing"
    CLOSED = "closed"


class SectorStatus(str, Enum):
    FORMING = "forming"
    ACTIVE = "active"
    CONTAINED = "contained"
    CLOSED = "closed"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class StageStatus(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    DONE = "done"


class CommandRole(str, Enum):
    COMMANDER = "commander"          # руководитель ликвидации / РТП
    DEPUTY = "deputy"                # заместитель


class ResourceMemberKind(str, Enum):
    UNIT = "unit"
    VEHICLE = "vehicle"
    PERSONNEL = "personnel"


class ZoneKind(str, Enum):
    HOT = "hot"                      # зона ЧС / очаг
    WARM = "warm"                    # зона проведения работ
    COLD = "cold"                    # зона обеспечения
    STAGING = "staging"              # зона сосредоточения резервов


class JournalKind(str, Enum):
    """The unified operational journal (§8) records both actions and decisions."""

    DECISION = "decision"            # решение руководителя (DecisionLog)
    ACTION = "action"                # действие / назначение (ActionLog)
    SITUATION = "situation"          # изменение оперативной обстановки
    ASSIGNMENT = "assignment"        # назначение подразделений
    INFO = "info"                    # получение информации


def values(enum_cls: type[Enum]) -> list[str]:
    return [e.value for e in enum_cls]
