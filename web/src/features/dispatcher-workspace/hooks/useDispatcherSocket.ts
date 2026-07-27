/**
 * useDispatcherSocket — binds the real-time channel to TanStack Query.
 *
 * Connects the singleton socket, feeds the current auth token, and translates
 * each server event into precise cache invalidations / updates so the whole
 * workspace stays live. Exposes the connection status for the UI indicator.
 *
 * When the socket cannot connect, nothing breaks: the query hooks keep polling
 * (their `refetchInterval`s), so the workspace degrades gracefully.
 */
import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/store/auth.store";
import { dispatcherSocket } from "../services/socket.service";
import { dispatcherKeys } from "./queryKeys";
import type { DispatcherEvent, LogEvent, LogLevel, SocketStatus } from "../types";

const MAX_LOG = 200;

function toLogLevel(raw: string): LogLevel {
  return raw === "critical" || raw === "warning" || raw === "success"
    ? raw
    : "info";
}

export function useDispatcherSocket(): { status: SocketStatus } {
  const qc = useQueryClient();
  const [status, setStatus] = useState<SocketStatus>(dispatcherSocket.getStatus());

  useEffect(() => {
    dispatcherSocket.setTokenProvider(() => useAuthStore.getState().accessToken);

    const offStatus = dispatcherSocket.onStatus(setStatus);
    const offEvent = dispatcherSocket.on((event: DispatcherEvent) => {
      switch (event.type) {
        case "incident.created":
          void qc.invalidateQueries({ queryKey: dispatcherKeys.activeIncidents() });
          void qc.invalidateQueries({ queryKey: dispatcherKeys.stats() });
          break;
        case "incident.updated":
        case "incident.status_changed":
          void qc.invalidateQueries({
            queryKey: dispatcherKeys.incident(event.payload.incident_id),
          });
          void qc.invalidateQueries({ queryKey: dispatcherKeys.activeIncidents() });
          void qc.invalidateQueries({ queryKey: dispatcherKeys.stats() });
          break;
        case "incident.deleted":
          void qc.invalidateQueries({ queryKey: dispatcherKeys.activeIncidents() });
          void qc.invalidateQueries({ queryKey: dispatcherKeys.stats() });
          qc.removeQueries({
            queryKey: dispatcherKeys.incident(event.payload.incident_id),
          });
          break;
        case "unit.updated":
          void qc.invalidateQueries({ queryKey: dispatcherKeys.units() });
          void qc.invalidateQueries({ queryKey: dispatcherKeys.resourceStatus() });
          void qc.invalidateQueries({ queryKey: dispatcherKeys.mapObjects() });
          void qc.invalidateQueries({ queryKey: dispatcherKeys.stats() });
          break;
        case "route.updated":
          void qc.invalidateQueries({
            queryKey: dispatcherKeys.incident(event.payload.incident_id),
          });
          break;
        case "log.appended": {
          const entry: LogEvent = {
            id: event.payload.id,
            occurred_at: event.payload.occurred_at,
            level: toLogLevel(event.payload.level),
            category: (event.payload.category as LogEvent["category"]) ?? "system",
            action: event.payload.action,
            message: event.payload.message,
            incident_id: event.payload.incident_id ?? null,
            unit_id: event.payload.unit_id ?? null,
          };
          qc.setQueryData<LogEvent[]>(dispatcherKeys.log(), (old) =>
            [entry, ...(old ?? [])].slice(0, MAX_LOG),
          );
          break;
        }
        default:
          break;
      }
    });

    dispatcherSocket.connect();

    return () => {
      offStatus();
      offEvent();
      // Keep the singleton alive across route changes within the app, but stop
      // listening; disconnect only when the whole workspace unmounts.
      dispatcherSocket.disconnect();
    };
  }, [qc]);

  return { status };
}
