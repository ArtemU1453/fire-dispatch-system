/**
 * WebSocket event contract for the dispatcher workspace.
 *
 * The backend real-time channel emits envelopes of the form
 * `{ type, payload }`. Every event below is handled by
 * `useDispatcherSocket`, which invalidates the relevant TanStack Query caches
 * and appends to the operational log.
 */
import type { IncidentStatus } from "./incident";

export type DispatcherEventType =
  | "incident.created"
  | "incident.updated"
  | "incident.status_changed"
  | "incident.deleted"
  | "unit.updated"
  | "route.updated"
  | "log.appended"
  | "pong";

export interface IncidentCreatedEvent {
  type: "incident.created";
  payload: { incident_id: string; number: string };
}

export interface IncidentUpdatedEvent {
  type: "incident.updated";
  payload: { incident_id: string };
}

export interface IncidentStatusChangedEvent {
  type: "incident.status_changed";
  payload: { incident_id: string; status: IncidentStatus };
}

export interface IncidentDeletedEvent {
  type: "incident.deleted";
  payload: { incident_id: string };
}

export interface UnitUpdatedEvent {
  type: "unit.updated";
  payload: { unit_id: string };
}

export interface RouteUpdatedEvent {
  type: "route.updated";
  payload: { incident_id: string; unit_id: string };
}

export interface LogAppendedEvent {
  type: "log.appended";
  payload: {
    id: string;
    occurred_at: string;
    level: string;
    category: string;
    action: string;
    message: string;
    incident_id?: string | null;
    unit_id?: string | null;
  };
}

export interface PongEvent {
  type: "pong";
  payload?: Record<string, never>;
}

export type DispatcherEvent =
  | IncidentCreatedEvent
  | IncidentUpdatedEvent
  | IncidentStatusChangedEvent
  | IncidentDeletedEvent
  | UnitUpdatedEvent
  | RouteUpdatedEvent
  | LogAppendedEvent
  | PongEvent;

export type SocketStatus =
  | "connecting"
  | "open"
  | "closed"
  | "reconnecting"
  | "disabled";
