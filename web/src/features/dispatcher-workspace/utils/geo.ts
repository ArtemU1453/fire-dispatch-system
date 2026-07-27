/**
 * Geo helpers shared by the map and its data layer. WGS-84 throughout;
 * OpenLayers projection conversion happens in the component with `fromLonLat`.
 */
import type { BBox, GeoPoint } from "../types";

/** Moscow city centre — a sensible default view for the МЧС workspace. */
export const DEFAULT_CENTER: GeoPoint = { longitude: 37.6173, latitude: 55.7558 };
export const DEFAULT_ZOOM = 11;

export function isValidCoord(
  lat: number | null | undefined,
  lon: number | null | undefined,
): lat is number {
  return (
    typeof lat === "number" &&
    typeof lon === "number" &&
    Number.isFinite(lat) &&
    Number.isFinite(lon) &&
    lat >= -90 &&
    lat <= 90 &&
    lon >= -180 &&
    lon <= 180
  );
}

/** Haversine distance in metres between two WGS-84 points. */
export function haversineMeters(a: GeoPoint, b: GeoPoint): number {
  const R = 6_371_000;
  const dLat = ((b.latitude - a.latitude) * Math.PI) / 180;
  const dLon = ((b.longitude - a.longitude) * Math.PI) / 180;
  const lat1 = (a.latitude * Math.PI) / 180;
  const lat2 = (b.latitude * Math.PI) / 180;
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.sin(dLon / 2) ** 2 * Math.cos(lat1) * Math.cos(lat2);
  return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
}

/** Bounding box grown by `paddingDeg` around a centre point. */
export function bboxAround(center: GeoPoint, paddingDeg = 0.25): BBox {
  return {
    minLon: center.longitude - paddingDeg,
    minLat: center.latitude - paddingDeg,
    maxLon: center.longitude + paddingDeg,
    maxLat: center.latitude + paddingDeg,
  };
}
