/**
 * Incident domain types for the dispatcher workspace.
 * These mirror the backend `app.incidents` schemas (value-based enums).
 */

export type IncidentStatus =
  | "created"
  | "checking"
  | "confirmed"
  | "selecting"
  | "dispatch_confirmed"
  | "dispatched"
  | "on_scene"
  | "localized"
  | "liquidated"
  | "completed"
  | "archived"
  | "cancelled";

export type IncidentPriority = "low" | "normal" | "high" | "critical";

export type IncidentCategory =
  | "fire"
  | "road_accident"
  | "rescue"
  | "chemical"
  | "wildfire"
  | "false_alarm"
  | "special_ops"
  | "service_ops"
  | "other";

export type IncidentSource =
  | "phone"
  | "radio"
  | "system"
  | "patrol"
  | "manual"
  | "other";

export type DispatchUnitStatus =
  | "assigned"
  | "en_route"
  | "on_scene"
  | "returning"
  | "released"
  | "cancelled";

export type TimelineEventType = string;

export interface IncidentSummary {
  id: string;
  number: string;
  category: IncidentCategory;
  status: IncidentStatus;
  priority: IncidentPriority;
  title: string | null;
  address: string | null;
  reported_at: string;
  /** Enriched client-side (assigned unit count) — optional. */
  assigned_count?: number;
}

export interface IncidentLocation {
  id: string;
  address: string | null;
  latitude: number | null;
  longitude: number | null;
  accuracy: string | null;
  source: string | null;
  is_primary: boolean;
}

export interface IncidentComment {
  id: string;
  author_name: string | null;
  text: string;
  created_at: string;
}

export interface TimelineEntry {
  id: string;
  event_type: TimelineEventType;
  title: string;
  detail: string | null;
  actor_name: string | null;
  meta: Record<string, unknown> | null;
  occurred_at: string;
}

export interface DispatchUnit {
  id: string;
  resource_id: string;
  role: string;
  status: DispatchUnitStatus;
  assigned_at: string;
  note: string | null;
  /** ETA in seconds, enriched client-side from the routing service. */
  eta_seconds?: number | null;
}

export interface Incident {
  id: string;
  number: string;
  category: IncidentCategory;
  source: IncidentSource;
  status: IncidentStatus;
  priority: IncidentPriority;
  title: string | null;
  description: string | null;
  address: string | null;
  latitude: number | null;
  longitude: number | null;
  danger_level: string | null;
  object_type: string | null;
  reporter_name: string | null;
  reporter_contact: string | null;
  reported_at: string;
  confirmed_at: string | null;
  closed_at: string | null;
  allowed_transitions: IncidentStatus[];
  locations: IncidentLocation[];
  comments: IncidentComment[];
  timeline: TimelineEntry[];
  dispatches: DispatchUnit[];
}

export interface IncidentTimeline {
  incident_id: string;
  count: number;
  entries: TimelineEntry[];
}

/** A unit assignment request payload. */
export interface AssignUnitInput {
  resource_id: string;
  role?: string;
  note?: string;
}
