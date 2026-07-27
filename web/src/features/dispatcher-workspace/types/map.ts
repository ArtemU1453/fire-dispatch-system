/**
 * Map domain types for the OpenLayers OperationalMap.
 */
import type { IncidentPriority } from "./incident";

/** Toggleable map layers. */
export type MapLayerId =
  | "incidents"
  | "units"
  | "routes"
  | "zones"
  | "hydrants"
  | "water_sources"
  | "closed_roads";

export type MapLayerVisibility = Record<MapLayerId, boolean>;

/** A generic geo point in WGS-84 (lon/lat order for OpenLayers `fromLonLat`). */
export interface GeoPoint {
  longitude: number;
  latitude: number;
}

/** Bounding box in WGS-84 degrees. */
export interface BBox {
  minLon: number;
  minLat: number;
  maxLon: number;
  maxLat: number;
}

export type MapObjectKind =
  | "incident"
  | "unit"
  | "hydrant"
  | "water_source"
  | "zone"
  | "closed_road";

/** A point feature rendered on the map. */
export interface MapPointFeature {
  id: string;
  kind: MapObjectKind;
  longitude: number;
  latitude: number;
  label: string;
  /** Domain-specific state used for styling (unit availability, priority…). */
  priority?: IncidentPriority;
  available?: boolean;
  /** Free-form details shown in the popup. */
  meta?: Record<string, string | number | null | undefined>;
}

/** A lat/lon point as returned by the routing service geometry. */
export interface RoutePointLike {
  latitude: number;
  longitude: number;
}

/** A route line (unit → incident), coordinates as [lon, lat] pairs. */
export interface MapRouteFeature {
  id: string;
  coordinates: Array<[number, number]>;
  label: string;
}

/** A responsibility zone / coverage polygon (rings of [lon, lat]). */
export interface MapZoneFeature {
  id: string;
  label: string;
  rings: Array<Array<[number, number]>>;
  color?: string;
}

/** The full feature set that OperationalMap renders. */
export interface MapFeatureSet {
  points: MapPointFeature[];
  routes: MapRouteFeature[];
  zones: MapZoneFeature[];
}
