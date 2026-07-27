/**
 * OpenLayers style factory for the OperationalMap. Colours resolve the shared
 * CSS palette at runtime so the map matches the active (dark/light) theme.
 */
import { Circle as CircleStyle, Fill, Stroke, Style, Text } from "ol/style";
import type { FeatureLike } from "ol/Feature";
import type { MapPointFeature } from "../types";

/** Read an HSL palette token from the document root as a usable CSS colour. */
function token(name: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  const raw = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
  return raw ? `hsl(${raw})` : fallback;
}

function incidentColor(feature: MapPointFeature): string {
  switch (feature.priority) {
    case "critical":
      return token("--danger", "#d7263d");
    case "high":
      return token("--warning", "#ffb703");
    case "normal":
      return token("--info", "#3a86ff");
    default:
      return token("--muted-foreground", "#8b98a8");
  }
}

function pointStyle(feature: MapPointFeature, selected: boolean): Style {
  const isIncident = feature.kind === "incident";
  const color = isIncident
    ? incidentColor(feature)
    : token("--success", "#2ec27e");
  const radius = isIncident ? 8 : 6;
  const strokeColor = selected ? token("--foreground", "#ffffff") : "#0e1621";
  return new Style({
    image: new CircleStyle({
      radius: selected ? radius + 2 : radius,
      fill: new Fill({ color }),
      stroke: new Stroke({ color: strokeColor, width: selected ? 3 : 1.5 }),
    }),
  });
}

/** Cluster bubble style (count badge). */
function clusterStyle(size: number): Style {
  const color = token("--primary", "#d7263d");
  return new Style({
    image: new CircleStyle({
      radius: 12 + Math.min(10, Math.log2(size) * 3),
      fill: new Fill({ color }),
      stroke: new Stroke({ color: "#ffffff", width: 2 }),
    }),
    text: new Text({
      text: String(size),
      fill: new Fill({ color: "#ffffff" }),
      font: "600 11px Inter, sans-serif",
    }),
  });
}

/**
 * Style function for the (clustered) point layer. Each rendered feature carries
 * an array of the underlying members under `features`.
 */
export function makePointStyle(selectedId: string | null) {
  return (feature: FeatureLike): Style => {
    const members = feature.get("features") as FeatureLike[] | undefined;
    if (members && members.length > 1) {
      return clusterStyle(members.length);
    }
    const single = members && members.length === 1 ? members[0] : feature;
    const data = single.get("data") as MapPointFeature | undefined;
    if (!data) return clusterStyle(members?.length ?? 1);
    return pointStyle(data, data.id === selectedId);
  };
}
