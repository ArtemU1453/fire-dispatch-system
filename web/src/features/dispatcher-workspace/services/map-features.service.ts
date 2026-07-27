/**
 * Pure transforms from domain objects to renderable map features. Kept free of
 * OpenLayers so they are trivially unit-testable; the component turns these into
 * OL geometries with `fromLonLat`.
 */
import type { SpatialObject } from "../api/map.service";
import { isValidCoord } from "../utils/geo";
import type {
  Incident,
  MapPointFeature,
  MapRouteFeature,
  RoutePointLike,
} from "../types";

export interface RoutePointLikeInternal {
  latitude: number;
  longitude: number;
}

/** Incident markers (only those with valid coordinates). */
export function buildIncidentPoints(incidents: Incident[]): MapPointFeature[] {
  const points: MapPointFeature[] = [];
  for (const inc of incidents) {
    if (!isValidCoord(inc.latitude, inc.longitude)) continue;
    points.push({
      id: `incident:${inc.id}`,
      kind: "incident",
      longitude: inc.longitude as number,
      latitude: inc.latitude as number,
      label: `№ ${inc.number}`,
      priority: inc.priority,
      meta: {
        Категория: inc.category,
        Статус: inc.status,
        Адрес: inc.address,
      },
    });
  }
  return points;
}

/** Unit markers from a spatial (bbox) search — resources with geometry. */
export function buildUnitPoints(objects: SpatialObject[]): MapPointFeature[] {
  const points: MapPointFeature[] = [];
  for (const obj of objects) {
    if (!isValidCoord(obj.latitude, obj.longitude)) continue;
    points.push({
      id: `unit:${obj.id}`,
      kind: "unit",
      longitude: obj.longitude as number,
      latitude: obj.latitude as number,
      label: obj.name ?? obj.code ?? "Подразделение",
      available: true,
      meta: { Код: obj.code },
    });
  }
  return points;
}

/** A route polyline from a routing-service geometry. */
export function buildRouteFeature(
  id: string,
  label: string,
  geometry: RoutePointLike[],
): MapRouteFeature | null {
  const coords: Array<[number, number]> = geometry
    .filter((p) => isValidCoord(p.latitude, p.longitude))
    .map((p) => [p.longitude, p.latitude]);
  if (coords.length < 2) return null;
  return { id, coordinates: coords, label };
}

/** A straight-line fallback route between two valid points. */
export function buildStraightRoute(
  id: string,
  label: string,
  from: RoutePointLike,
  to: RoutePointLike,
): MapRouteFeature | null {
  if (!isValidCoord(from.latitude, from.longitude)) return null;
  if (!isValidCoord(to.latitude, to.longitude)) return null;
  return {
    id,
    label,
    coordinates: [
      [from.longitude, from.latitude],
      [to.longitude, to.latitude],
    ],
  };
}
