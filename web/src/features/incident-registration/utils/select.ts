/**
 * Converters from API result shapes into the store's `SelectedUnit`.
 */
import type { NearestResource, RecommendedUnit, SelectedUnit } from "../types";

export function recommendedToSelected(unit: RecommendedUnit): SelectedUnit {
  return {
    resource_id: unit.resource_id,
    code: unit.code,
    name: unit.name,
    role: unit.role,
    distance_meters: unit.distance_meters,
    eta_seconds: unit.eta_seconds ?? null,
    reasons: unit.reasons,
  };
}

export function nearestToSelected(res: NearestResource): SelectedUnit {
  return {
    resource_id: res.id,
    code: res.code,
    name: res.name,
    role: "primary",
    distance_meters: res.distance_meters,
    eta_seconds: null,
    reasons: ["Добавлено диспетчером"],
  };
}
