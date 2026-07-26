"""Enumerations for the simulation & training platform (Stage 17).

These types belong to the **training contour** only. They intentionally do not
reuse the production incident/resource enums so that the simulator can evolve
independently and can never be confused with, or coupled to, the live system.
"""

from __future__ import annotations

import enum


class SimulationMode(str, enum.Enum):
    """How a training session behaves."""

    TRAINING = "training"      # guided: hints and feedback are available
    EXAM = "exam"              # graded: no hints, actions scored strictly
    FREE = "free"              # sandbox: free modelling, no grading pressure
    REPLAY = "replay"          # replay a recorded (or real) incident timeline


class SessionState(str, enum.Enum):
    """Lifecycle of a running session."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"        # ended early by the instructor/trainee
    COMPLETED = "completed"    # scenario ran to its natural end


class SimIncidentType(str, enum.Enum):
    """Kinds of simulated incident the generator can produce."""

    FIRE = "fire"                       # пожар
    TRAFFIC_ACCIDENT = "traffic_accident"  # ДТП
    TECHNOGENIC = "technogenic"         # авария (техногенная)
    FALSE_ALARM = "false_alarm"         # ложный вызов
    HAZMAT = "hazmat"                   # выброс опасных веществ
    RESCUE = "rescue"                   # спасательные работы


class SimIncidentStatus(str, enum.Enum):
    PENDING = "pending"          # awaiting the dispatcher's decision
    DISPATCHED = "dispatched"    # units assigned, en route/working
    RESOLVED = "resolved"        # handled successfully
    EXPIRED = "expired"          # deadline passed without adequate response


class SimUnitStatus(str, enum.Enum):
    AVAILABLE = "available"      # ready to be dispatched
    BUSY = "busy"                # assigned to an incident
    BROKEN = "broken"            # поломка техники
    UNAVAILABLE = "unavailable"  # otherwise not dispatchable


class SimUnitCategory(str, enum.Enum):
    """Coarse capability categories for simulated units."""

    FIRE = "fire"                # пожарные расчёты
    RESCUE = "rescue"            # аварийно-спасательные
    MEDICAL = "medical"          # медицинские
    HAZMAT = "hazmat"            # химзащита
    SPECIAL = "special"          # специальная техника


class EventType(str, enum.Enum):
    """Scheduled world events applied by the engine as time advances."""

    SPAWN_INCIDENT = "spawn_incident"
    UNIT_BREAKDOWN = "unit_breakdown"       # поломка техники
    UNIT_REPAIR = "unit_repair"
    UNIT_UNAVAILABLE = "unit_unavailable"   # недоступность ресурса
    UNIT_AVAILABLE = "unit_available"
    ROAD_CLOSURE = "road_closure"           # закрытие дорог
    ROAD_REOPEN = "road_reopen"
    WEATHER_CHANGE = "weather_change"       # изменение погодных условий
    MESSAGE = "message"                     # instructor injection / narrative


class ActionType(str, enum.Enum):
    """Actions a trainee dispatcher can take during a session."""

    DISPATCH = "dispatch"            # assign units to an incident
    REASSIGN = "reassign"           # change a previous dispatch decision
    ACKNOWLEDGE = "acknowledge"     # accept/annotate an incident
    RESOLVE = "resolve"             # mark an incident handled
    ESCALATE = "escalate"           # request more resources


class Weather(str, enum.Enum):
    CLEAR = "clear"
    RAIN = "rain"
    SNOW = "snow"
    FOG = "fog"
    STORM = "storm"
