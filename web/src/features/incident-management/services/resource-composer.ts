/**
 * Composes the "Assigned Resources" rows from the incident's dispatch records
 * enriched with live unit metadata. Pure and unit-testable.
 *
 * A dispatch record carries a `resource_id`; it is matched to a unit by unit id
 * or by the unit's vehicle resource id. Unmatched rows still render (from the
 * dispatch record) but unit-centric actions are disabled for them.
 */
import type { DispatchUnit, Incident } from "@/features/dispatcher-workspace/types";
import type { Unit } from "@/features/dispatcher-workspace/types/resource";
import type { AssignedResource, UnitStatusOption } from "../types";

function matchUnit(dispatch: DispatchUnit, units: Unit[]): Unit | null {
  return (
    units.find(
      (u) =>
        u.id === dispatch.resource_id ||
        u.vehicle_resource_id === dispatch.resource_id,
    ) ?? null
  );
}

function toStatusOption(unit: Unit | null): UnitStatusOption | null {
  if (!unit?.status) return null;
  return {
    code: unit.status.code,
    name: unit.status.name,
    color: unit.status.color,
    isAvailableForDispatch: unit.status.is_available_for_dispatch,
  };
}

export function composeAssignedResources(
  incident: Incident,
  units: Unit[],
): AssignedResource[] {
  return incident.dispatches.map((d) => {
    const unit = matchUnit(d, units);
    return {
      resourceId: d.resource_id,
      unitId: unit?.id ?? null,
      code: unit?.code ?? d.resource_id.slice(0, 8),
      name: unit?.name ?? "Подразделение",
      callSign: unit?.call_sign ?? null,
      role: d.role,
      dispatchStatus: d.status,
      unitStatus: toStatusOption(unit),
      vehicleType: unit?.organization?.name ?? null,
      crewCount: unit?.crew_count ?? 0,
      assignedAt: d.assigned_at,
      departedAt: null,
      arrivedAt: null,
      etaSeconds: d.eta_seconds ?? null,
      speedKmh: null,
    };
  });
}
