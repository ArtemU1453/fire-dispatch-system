"""Strategic scenario format (Stage 18 §4, §10).

A scenario is a serialisable list of **modifications** applied to a baseline
digital model to explore an infrastructure-development option. Applying a
scenario always produces a *new* model — the baseline is never mutated, so the
live system and the reference model are untouched.
"""

from __future__ import annotations

import enum
from dataclasses import asdict, dataclass, field
from typing import Any

SCENARIO_FORMAT_VERSION = 1


class ModificationType(str, enum.Enum):
    OPEN_STATION = "open_station"        # открытие нового подразделения
    CLOSE_STATION = "close_station"      # закрытие подразделения
    DEPOT_REPAIR = "depot_repair"        # ремонт депо (временное отключение)
    ROAD_CHANGE = "road_change"          # изменение дорог (скорость/фактор)
    NEW_OBJECT = "new_object"            # строительство нового объекта защиты
    CHANGE_NORM = "change_norm"          # изменение нормативов выезда


@dataclass
class Modification:
    """A single change to apply. ``params`` are type-specific."""

    type: str
    params: dict[str, Any] = field(default_factory=dict)
    note: str = ""


@dataclass
class Scenario:
    id: str
    title: str
    description: str = ""
    objectives: list[str] = field(default_factory=list)
    modifications: list[Modification] = field(default_factory=list)
    format_version: int = SCENARIO_FORMAT_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Scenario:
        return cls(
            id=str(data["id"]),
            title=str(data.get("title", data["id"])),
            description=str(data.get("description", "")),
            objectives=list(data.get("objectives", [])),
            modifications=[
                Modification(
                    type=str(m["type"]),
                    params=dict(m.get("params", {})),
                    note=str(m.get("note", "")),
                )
                for m in data.get("modifications", [])
            ],
            format_version=int(data.get("format_version", SCENARIO_FORMAT_VERSION)),
        )
