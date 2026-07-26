"""Apply a strategic scenario to a baseline model (Stage 18 §4, §9).

``apply_scenario`` returns a **new** :class:`TwinModel` — a deep copy with the
scenario's modifications applied. The baseline is never mutated, guaranteeing the
reference model (and, by construction, the live system) is untouched.
"""

from __future__ import annotations

from app.digital_twin.scenarios.schema import (
    Modification,
    ModificationType,
    Scenario,
)
from app.digital_twin.simulation.model import (
    ProtectedObject,
    Station,
    StationCategory,
    TwinModel,
)


class ScenarioApplicationError(ValueError):
    """Raised when a modification cannot be applied to the model."""


def apply_scenario(baseline: TwinModel, scenario: Scenario) -> TwinModel:
    model = baseline.copy(name=f"scenario:{scenario.id}")
    for mod in scenario.modifications:
        _apply_modification(model, mod)
    return model


def _apply_modification(model: TwinModel, mod: Modification) -> None:
    try:
        mtype = ModificationType(mod.type)
    except ValueError as exc:
        raise ScenarioApplicationError(f"unknown modification: {mod.type}") from exc
    p = mod.params

    if mtype == ModificationType.OPEN_STATION:
        sid = str(p["id"])
        if sid in model.stations:
            raise ScenarioApplicationError(f"station already exists: {sid}")
        model.stations[sid] = Station(
            id=sid,
            name=str(p.get("name", sid)),
            x=float(p["x"]),
            y=float(p["y"]),
            category=StationCategory(p.get("category", StationCategory.FIRE.value)),
            units=int(p.get("units", 1)),
            active=True,
        )
    elif mtype == ModificationType.CLOSE_STATION:
        _station(model, p).active = False
    elif mtype == ModificationType.DEPOT_REPAIR:
        # Temporary closure for the analysis horizon — same effect on coverage.
        _station(model, p).active = False
    elif mtype == ModificationType.ROAD_CHANGE:
        if "speed_multiplier" in p:
            model.road.speed_multiplier = float(p["speed_multiplier"])
        if "road_factor" in p:
            model.road.road_factor = float(p["road_factor"])
        if "base_speed_kmh" in p:
            model.road.base_speed_kmh = float(p["base_speed_kmh"])
    elif mtype == ModificationType.NEW_OBJECT:
        oid = str(p["id"])
        model.protected_objects[oid] = ProtectedObject(
            id=oid,
            name=str(p.get("name", oid)),
            x=float(p["x"]),
            y=float(p["y"]),
            risk_class=int(p.get("risk_class", 1)),
        )
    elif mtype == ModificationType.CHANGE_NORM:
        norm = float(p["norm_time_s"])
        district_id = p.get("district_id")
        if district_id is not None:
            if district_id not in model.districts:
                raise ScenarioApplicationError(f"unknown district: {district_id}")
            model.districts[district_id].norm_time_s = norm
        else:
            for d in model.districts.values():
                d.norm_time_s = norm


def _station(model: TwinModel, params: dict) -> Station:
    sid = str(params.get("id", ""))
    station = model.stations.get(sid)
    if station is None:
        raise ScenarioApplicationError(f"unknown station: {sid}")
    return station
