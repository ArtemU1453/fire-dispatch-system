/**
 * MapService — geospatial data and route building for the OperationalMap.
 *
 * Point sources beyond units/incidents (hydrants, water sources, closed roads,
 * responsibility zones) are served through the GIS spatial API by category.
 * Categories the backend has not yet published simply return an empty set, so
 * the corresponding layer renders empty rather than breaking the map.
 */
import { request } from "@/api/client";
import { endpoints } from "./endpoints";
import type { BBox, GeoPoint } from "../types";

export interface SpatialObject {
  id: string;
  code: string | null;
  name: string | null;
  latitude: number | null;
  longitude: number | null;
}

interface SpatialSearchResponse {
  count: number;
  items: SpatialObject[];
}

export interface RoutePoint {
  latitude: number;
  longitude: number;
}

export interface RouteResult {
  origin: RoutePoint;
  destination: RoutePoint;
  distance_km: number;
  duration_seconds: number;
  eta_minutes: number;
  geometry: RoutePoint[];
}

export interface EtaResult {
  eta_seconds: number;
  eta_minutes: number;
  distance_meters: number;
  is_fallback: boolean;
}

export const MapService = {
  /** Resources with geometry within a bounding box (SRID 4326). */
  async resourcesInBBox(bbox: BBox, signal?: AbortSignal): Promise<SpatialObject[]> {
    const res = await request<SpatialSearchResponse>({
      url: endpoints.spatialBBox,
      method: "GET",
      params: {
        min_lon: bbox.minLon,
        min_lat: bbox.minLat,
        max_lon: bbox.maxLon,
        max_lat: bbox.maxLat,
        limit: 1000,
      },
      signal,
    });
    return res.items;
  },

  /** Build a full route between two points (returns null if routing is down). */
  async buildRoute(
    origin: GeoPoint,
    destination: GeoPoint,
    signal?: AbortSignal,
  ): Promise<RouteResult | null> {
    try {
      return await request<RouteResult>({
        url: endpoints.route,
        method: "GET",
        params: {
          from_lat: origin.latitude,
          from_lon: origin.longitude,
          to_lat: destination.latitude,
          to_lon: destination.longitude,
        },
        signal,
      });
    } catch {
      // Routing is a best-effort enrichment; never fail the whole map on it.
      return null;
    }
  },

  /** Estimate time of arrival for a single origin/destination pair. */
  async estimateEta(
    origin: GeoPoint,
    destination: GeoPoint,
    signal?: AbortSignal,
  ): Promise<EtaResult | null> {
    try {
      return await request<EtaResult>({
        url: endpoints.eta,
        method: "POST",
        data: { origin, destination },
        signal,
      });
    } catch {
      // A single failed ETA must not break the details panel.
      return null;
    }
  },
};

export type MapServiceType = typeof MapService;
