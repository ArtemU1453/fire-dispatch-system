// Server-produced DTOs the apps render (Stage 19). These mirror the backend
// mobile schemas exactly; the apps never compute these — the server does.

export interface Incident {
  id: string;
  category: string;
  priority: string;
  status: string;
  address: string;
  description: string;
  lat: number | null;
  lon: number | null;
  created_at: string;
  recommended_units: string[];
  assigned_unit_ids: string[];
}

export interface Resource {
  unit_id: string;
  name: string;
  category: string;
  status: string;
  busy: boolean;
  lat?: number | null;
  lon?: number | null;
}

export interface Summary {
  active_incidents: number;
  available_units: number;
  busy_units: number;
  calls_today: number;
}

export interface Critical {
  id: string;
  type: string;
  message: string;
  created_at: string;
  incident_id?: string | null;
  severity: string;
}

export interface Dashboard {
  summary: Summary;
  active_incidents: Incident[];
  resource_load: Resource[];
  critical: Critical[];
}

export interface RoutePoint {
  lat: number;
  lon: number;
}

export interface Route {
  points: RoutePoint[];
  distance_km: number;
  eta_seconds: number | null;
}

export interface Dispatch {
  incident_id: string;
  address: string;
  description: string;
  category: string;
  priority: string;
  recommended_composition: string[];
  contact?: string | null;
  lat?: number | null;
  lon?: number | null;
  current_status: string;
}

export type ResponderStatus =
  | "assigned"
  | "en_route"
  | "on_scene"
  | "working"
  | "returning"
  | "completed";

export interface SyncOperation {
  op_id: string;
  type: "status" | "message";
  payload: Record<string, unknown>;
}

export interface SyncResult {
  op_id: string;
  applied: boolean;
  duplicate: boolean;
  error?: string | null;
  result?: Record<string, unknown> | null;
}
