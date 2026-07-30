/**
 * Binds the incident-scoped realtime channel to TanStack Query: every mapped
 * event invalidates the relevant management caches so the screen updates without
 * a reload. Falls back to query polling when the socket is down.
 */
import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/store/auth.store";
import { dispatcherSocket } from "@/features/dispatcher-workspace/services/socket.service";
import { incidentRealtime, type RealtimeEvent } from "../services";
import { managementKeys } from "./keys";
import type { SocketStatus } from "@/features/dispatcher-workspace/types";

export function useIncidentRealtime(incidentId: string): { status: SocketStatus } {
  const qc = useQueryClient();
  const [status, setStatus] = useState<SocketStatus>(incidentRealtime.getStatus());

  useEffect(() => {
    if (!incidentId) return;
    dispatcherSocket.setTokenProvider(() => useAuthStore.getState().accessToken);

    const offStatus = incidentRealtime.onStatus(setStatus);
    const offEvent = incidentRealtime.subscribe(incidentId, (event: RealtimeEvent) => {
      switch (event.type) {
        case "ResourceAssigned":
        case "ResourceReleased":
        case "ResourceStatusChanged":
          void qc.invalidateQueries({ queryKey: managementKeys.incident(incidentId) });
          void qc.invalidateQueries({ queryKey: managementKeys.units() });
          void qc.invalidateQueries({ queryKey: managementKeys.timeline(incidentId) });
          break;
        case "IncidentUpdated":
        case "IncidentClosed":
          void qc.invalidateQueries({ queryKey: managementKeys.incident(incidentId) });
          void qc.invalidateQueries({ queryKey: managementKeys.timeline(incidentId) });
          break;
        case "ETAChanged":
          void qc.invalidateQueries({ queryKey: managementKeys.incident(incidentId) });
          break;
        case "MessageReceived":
          void qc.invalidateQueries({ queryKey: managementKeys.timeline(incidentId) });
          break;
      }
    });

    incidentRealtime.connect();
    return () => {
      offStatus();
      offEvent();
    };
  }, [incidentId, qc]);

  return { status };
}
