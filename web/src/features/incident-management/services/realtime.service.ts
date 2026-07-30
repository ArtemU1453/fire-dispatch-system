/**
 * IncidentRealtimeService — the incident-scoped real-time channel.
 *
 * Reuses the existing dispatcher WebSocket (Stage 2 `dispatcherSocket`, with its
 * reconnect + heartbeat) rather than opening a second connection, and maps the
 * transport events onto the operational-management semantics for one incident:
 *
 *   ResourceAssigned · ResourceStatusChanged · IncidentUpdated ·
 *   MessageReceived · ETAChanged · IncidentClosed · ResourceReleased
 */
import { dispatcherSocket } from "@/features/dispatcher-workspace/services/socket.service";
import { isClosedStatus } from "@/features/dispatcher-workspace/utils/format";
import type {
  DispatcherEvent,
  SocketStatus,
} from "@/features/dispatcher-workspace/types";
import type { IncidentStatus } from "../types";

export type RealtimeEventType =
  | "ResourceAssigned"
  | "ResourceStatusChanged"
  | "IncidentUpdated"
  | "MessageReceived"
  | "ETAChanged"
  | "IncidentClosed"
  | "ResourceReleased";

export interface RealtimeEvent {
  type: RealtimeEventType;
  incidentId: string;
}

function mapEvent(incidentId: string, event: DispatcherEvent): RealtimeEvent | null {
  switch (event.type) {
    case "incident.status_changed":
      if (event.payload.incident_id !== incidentId) return null;
      return {
        type: isClosedStatus(event.payload.status as IncidentStatus)
          ? "IncidentClosed"
          : "IncidentUpdated",
        incidentId,
      };
    case "incident.updated":
      return event.payload.incident_id === incidentId
        ? { type: "IncidentUpdated", incidentId }
        : null;
    case "incident.deleted":
      return event.payload.incident_id === incidentId
        ? { type: "IncidentClosed", incidentId }
        : null;
    case "unit.updated":
      // Unit lifecycle changes affect the assigned-resources view.
      return { type: "ResourceStatusChanged", incidentId };
    case "route.updated":
      return event.payload.incident_id === incidentId
        ? { type: "ETAChanged", incidentId }
        : null;
    case "log.appended":
      return event.payload.incident_id == null ||
        event.payload.incident_id === incidentId
        ? { type: "MessageReceived", incidentId }
        : null;
    default:
      return null;
  }
}

export class IncidentRealtimeService {
  /** Ensure the shared channel is connected. */
  connect(): void {
    dispatcherSocket.connect();
  }

  getStatus(): SocketStatus {
    return dispatcherSocket.getStatus();
  }

  onStatus(handler: (s: SocketStatus) => void): () => void {
    return dispatcherSocket.onStatus(handler);
  }

  /** Subscribe to mapped events for a single incident. */
  subscribe(incidentId: string, handler: (e: RealtimeEvent) => void): () => void {
    return dispatcherSocket.on((event) => {
      const mapped = mapEvent(incidentId, event);
      if (mapped) handler(mapped);
    });
  }
}

export const incidentRealtime = new IncidentRealtimeService();
export { mapEvent as __mapEventForTest };
