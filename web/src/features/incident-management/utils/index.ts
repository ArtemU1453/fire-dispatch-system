/**
 * Presentation + filtering helpers. Incident label/format helpers are reused
 * from the dispatcher-workspace feature (DRY).
 */
export {
  statusLabel,
  priorityLabel,
  categoryLabel,
  priorityVariant,
  isClosedStatus,
  formatEta,
  timeAgo,
} from "@/features/dispatcher-workspace/utils/format";

import type { BadgeVariant } from "@/features/dispatcher-workspace/utils/format";
import type { TimelineCategory, TimelineEntry, DispatchUnitStatus } from "../types";

/** Russian labels for the incident-side dispatch status. */
export const DISPATCH_STATUS_LABELS: Record<DispatchUnitStatus, string> = {
  assigned: "Назначено",
  en_route: "Выезд",
  on_scene: "На месте",
  returning: "Возвращается",
  released: "Освобождено",
  cancelled: "Отменено",
};

export function dispatchStatusLabel(status: string): string {
  return DISPATCH_STATUS_LABELS[status as DispatchUnitStatus] ?? status;
}

export function dispatchStatusVariant(status: string): BadgeVariant {
  switch (status) {
    case "on_scene":
      return "success";
    case "en_route":
      return "info";
    case "assigned":
      return "warning";
    case "cancelled":
    case "released":
      return "outline";
    default:
      return "default";
  }
}

/** Classify a timeline event into a filterable category. */
export function timelineCategory(eventType: string): Exclude<TimelineCategory, "all"> {
  const t = eventType.toLowerCase();
  if (t.includes("regist") || t === "created") return "registration";
  if (t.includes("assign") || t.includes("unit") || t.includes("dispatch"))
    return "assignment";
  if (t.includes("status") || t.includes("localiz") || t.includes("liquidat"))
    return "status";
  if (t.includes("route") || t.includes("eta")) return "route";
  if (t.includes("comment") || t.includes("message")) return "message";
  return "decision";
}

/** Filter + search the timeline entries. */
export function filterTimeline(
  entries: TimelineEntry[],
  search: string,
  category: TimelineCategory,
): TimelineEntry[] {
  const q = search.trim().toLowerCase();
  return entries.filter((e) => {
    if (category !== "all" && timelineCategory(e.event_type) !== category) return false;
    if (q) {
      const hay = `${e.title} ${e.detail ?? ""} ${e.actor_name ?? ""}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
}

/** Speed (km/h) from two positions, or null when not derivable. */
export function speedKmh(
  prev: { latitude: number; longitude: number; recorded_at: string | null } | null,
  next: { latitude: number; longitude: number; recorded_at: string | null } | null,
): number | null {
  if (!prev || !next || !prev.recorded_at || !next.recorded_at) return null;
  const dt =
    (new Date(next.recorded_at).getTime() - new Date(prev.recorded_at).getTime()) / 1000;
  if (dt <= 0) return null;
  const R = 6_371_000;
  const dLat = ((next.latitude - prev.latitude) * Math.PI) / 180;
  const dLon = ((next.longitude - prev.longitude) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((prev.latitude * Math.PI) / 180) *
      Math.cos((next.latitude * Math.PI) / 180) *
      Math.sin(dLon / 2) ** 2;
  const meters = 2 * R * Math.asin(Math.min(1, Math.sqrt(a)));
  return Math.round((meters / dt) * 3.6);
}
