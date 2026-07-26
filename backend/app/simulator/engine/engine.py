"""The simulation engine (Stage 17).

Drives a single training session: it owns the world, the clock and the event
queue, applies scheduled events as time advances, evolves dispatched incidents
to resolution, expires neglected ones, and accepts trainee actions (dispatch,
reassign, resolve). Everything is in-memory and deterministic — no database, no
production models — so a scenario always replays identically.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.simulator.engine.clock import SimulationClock
from app.simulator.engine.enums import (
    ActionType,
    EventType,
    SimIncidentStatus,
    SimUnitCategory,
    SimUnitStatus,
    Weather,
)
from app.simulator.engine.world import (
    SimIncident,
    SimUnit,
    WorldState,
    travel_time_s,
)
from app.simulator.events.definitions import ScheduledEvent
from app.simulator.events.queue import EventQueue
from app.simulator.players.actions import ActionOutcome, ActionRecord

# Time a unit spends working an incident once it arrives, scaled by severity.
_BASE_SERVICE_S = 180.0
# Weather slows travel: multiplier applied to travel time.
_WEATHER_FACTOR = {
    Weather.CLEAR: 1.0,
    Weather.RAIN: 1.15,
    Weather.FOG: 1.3,
    Weather.SNOW: 1.4,
    Weather.STORM: 1.6,
}


@dataclass
class Engine:
    world: WorldState = field(default_factory=WorldState)
    clock: SimulationClock = field(default_factory=SimulationClock)
    queue: EventQueue = field(default_factory=EventQueue)
    actions: list[ActionRecord] = field(default_factory=list)
    applied_events: list[ScheduledEvent] = field(default_factory=list)
    _action_seq: int = 0
    # Planned resolution time per dispatched incident (sim seconds).
    _resolve_at: dict[str, float] = field(default_factory=dict)

    # ------------------------------------------------------------------ time
    def advance(self, sim_seconds: float) -> None:
        """Advance the clock and apply everything that becomes due."""
        target = self.clock.advance(sim_seconds)
        self._process_until(target)

    def step(self) -> None:
        """Advance by one fixed step and apply due changes."""
        target = self.clock.step()
        self._process_until(target)

    def run_to_end(self, max_iterations: int = 10_000) -> None:
        """Advance in steps until no events remain and no incidents are active."""
        iterations = 0
        while not self.is_finished and iterations < max_iterations:
            self.step()
            iterations += 1

    def _process_until(self, now: float) -> None:
        for event in self.queue.pop_due(now):
            self._apply_event(event)
            self.applied_events.append(event)
        self._progress_incidents(now)

    # ---------------------------------------------------------------- events
    def _apply_event(self, event: ScheduledEvent) -> None:
        p = event.payload
        t = event.type
        if t == EventType.SPAWN_INCIDENT:
            self.world.add_incident(_incident_from_payload(p, event.time_s))
        elif t == EventType.UNIT_BREAKDOWN:
            self._set_unit_status(p.get("unit_id"), SimUnitStatus.BROKEN)
        elif t == EventType.UNIT_REPAIR:
            self._set_unit_status(p.get("unit_id"), SimUnitStatus.AVAILABLE)
        elif t == EventType.UNIT_UNAVAILABLE:
            self._set_unit_status(p.get("unit_id"), SimUnitStatus.UNAVAILABLE)
        elif t == EventType.UNIT_AVAILABLE:
            self._set_unit_status(p.get("unit_id"), SimUnitStatus.AVAILABLE)
        elif t == EventType.ROAD_CLOSURE:
            if road := p.get("road"):
                self.world.closed_roads.add(str(road))
        elif t == EventType.ROAD_REOPEN:
            self.world.closed_roads.discard(str(p.get("road")))
        elif t == EventType.WEATHER_CHANGE:
            self.world.weather = Weather(p.get("weather", Weather.CLEAR.value))
        # MESSAGE events carry only narrative; nothing to mutate.

    def _set_unit_status(self, unit_id: str | None, status: SimUnitStatus) -> None:
        if unit_id and (unit := self.world.units.get(unit_id)):
            # Do not steal a unit that is actively assigned unless it breaks.
            if status == SimUnitStatus.BROKEN or unit.assigned_incident_id is None:
                unit.status = status

    # ------------------------------------------------------------- incidents
    def _progress_incidents(self, now: float) -> None:
        for inc in list(self.world.incidents.values()):
            if inc.status == SimIncidentStatus.PENDING:
                if now - inc.created_at > inc.response_deadline_s:
                    inc.status = SimIncidentStatus.EXPIRED
            elif inc.status == SimIncidentStatus.DISPATCHED:
                due = self._resolve_at.get(inc.id)
                if due is not None and now >= due:
                    self._resolve_incident(inc, now)

    def _resolve_incident(self, inc: SimIncident, now: float) -> None:
        inc.status = SimIncidentStatus.RESOLVED
        inc.resolved_at = now
        for uid in inc.dispatched_unit_ids:
            if unit := self.world.units.get(uid):
                unit.status = SimUnitStatus.AVAILABLE
                unit.assigned_incident_id = None
        self._resolve_at.pop(inc.id, None)

    # --------------------------------------------------------------- actions
    def dispatch(self, incident_id: str, unit_ids: list[str]) -> ActionOutcome:
        """Trainee assigns units to a pending incident."""
        inc = self.world.incidents.get(incident_id)
        if inc is None:
            return self._record_reject(
                ActionType.DISPATCH, incident_id, unit_ids, "unknown incident"
            )
        if inc.status not in (SimIncidentStatus.PENDING, SimIncidentStatus.DISPATCHED):
            return self._record_reject(
                ActionType.DISPATCH, incident_id, unit_ids,
                f"incident is {inc.status.value}",
            )
        units = [self.world.units.get(uid) for uid in unit_ids]
        if any(u is None for u in units):
            return self._record_reject(
                ActionType.DISPATCH, incident_id, unit_ids, "unknown unit"
            )
        not_ready = [u for u in units if u and not u.dispatchable]
        if not_ready:
            return self._record_reject(
                ActionType.DISPATCH, incident_id, unit_ids,
                f"unit not available: {not_ready[0].id}",
            )
        action_type = (
            ActionType.REASSIGN
            if inc.status == SimIncidentStatus.DISPATCHED
            else ActionType.DISPATCH
        )
        self._assign(inc, [u for u in units if u])
        self._record(action_type, incident_id, unit_ids)
        return ActionOutcome(True, "dispatched", incident_id)

    def resolve(self, incident_id: str) -> ActionOutcome:
        inc = self.world.incidents.get(incident_id)
        if inc is None or inc.status != SimIncidentStatus.DISPATCHED:
            return self._record_reject(
                ActionType.RESOLVE, incident_id, [], "not dispatched"
            )
        self._resolve_incident(inc, self.clock.time_s)
        self._record(ActionType.RESOLVE, incident_id, [])
        return ActionOutcome(True, "resolved", incident_id)

    def _assign(self, inc: SimIncident, units: list[SimUnit]) -> None:
        # Free any previously assigned units (reassignment).
        for uid in inc.dispatched_unit_ids:
            if (prev := self.world.units.get(uid)) and prev not in units:
                prev.status = SimUnitStatus.AVAILABLE
                prev.assigned_incident_id = None
        now = self.clock.time_s
        inc.dispatched_unit_ids = [u.id for u in units]
        inc.status = SimIncidentStatus.DISPATCHED
        inc.dispatched_at = now
        wf = _WEATHER_FACTOR.get(self.world.weather, 1.0)
        arrival = max(
            (travel_time_s(u, inc.x, inc.y) * wf for u in units), default=0.0
        )
        for u in units:
            u.status = SimUnitStatus.BUSY
            u.assigned_incident_id = inc.id
        self._resolve_at[inc.id] = now + arrival + _BASE_SERVICE_S * inc.severity

    # --------------------------------------------------------------- records
    def _record(
        self, type_: ActionType, incident_id: str | None, unit_ids: list[str]
    ) -> None:
        self.actions.append(
            ActionRecord(
                seq=self._action_seq,
                time_s=self.clock.time_s,
                type=type_,
                incident_id=incident_id,
                unit_ids=tuple(unit_ids),
            )
        )
        self._action_seq += 1

    def _record_reject(
        self,
        type_: ActionType,
        incident_id: str | None,
        unit_ids: list[str],
        reason: str,
    ) -> ActionOutcome:
        # Rejected attempts are still recorded (they count as errors in scoring).
        self.actions.append(
            ActionRecord(
                seq=self._action_seq,
                time_s=self.clock.time_s,
                type=type_,
                incident_id=incident_id,
                unit_ids=tuple(unit_ids),
                note=f"rejected: {reason}",
            )
        )
        self._action_seq += 1
        return ActionOutcome(False, reason, incident_id)

    # ---------------------------------------------------------------- status
    @property
    def is_finished(self) -> bool:
        return self.queue.is_empty() and not self.world.active_incidents()

    def seed_units(self, units: list[SimUnit]) -> None:
        for u in units:
            self.world.add_unit(u)

    def add_category_alias(self, category: SimUnitCategory) -> None:  # pragma: no cover
        """Reserved hook for future category mapping; intentionally a no-op."""
        return None


def _incident_from_payload(p: dict, time_s: float) -> SimIncident:
    from app.simulator.engine.enums import SimIncidentType

    return SimIncident(
        id=str(p["id"]),
        type=SimIncidentType(p.get("type", SimIncidentType.FIRE.value)),
        x=float(p.get("x", 0.0)),
        y=float(p.get("y", 0.0)),
        severity=int(p.get("severity", 1)),
        required_units=int(p.get("required_units", 1)),
        required_category=SimUnitCategory(
            p.get("required_category", SimUnitCategory.FIRE.value)
        ),
        created_at=time_s,
        response_deadline_s=float(p.get("response_deadline_s", 120.0)),
        is_false_alarm=bool(p.get("is_false_alarm", False)),
        label=str(p.get("label", "")),
    )
