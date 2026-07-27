export * from "./labels";
export * from "./select";

/** True when both lat/lon are finite and in valid WGS-84 range. */
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
