/**
 * Data hooks for the management screen — incident card, timeline, assigned
 * resources (composed) and the availability-status catalog. All auto-refresh
 * (polling fallback) and are kept live by the realtime layer.
 */
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { env } from "@/lib/env";
import { ManagementService } from "../api";
import { composeAssignedResources } from "../services";
import { managementKeys } from "./keys";
import type { AssignedResource, Incident, IncidentTimeline, UnitStatusOption } from "../types";
import type { Unit } from "@/features/dispatcher-workspace/types/resource";

export function useIncident(incidentId: string) {
  return useQuery<Incident>({
    queryKey: managementKeys.incident(incidentId),
    queryFn: ({ signal }) => ManagementService.getIncident(incidentId, signal),
    enabled: Boolean(incidentId),
    refetchInterval: env.pollIncidents,
    staleTime: env.pollIncidents / 2,
  });
}

export function useTimeline(incidentId: string) {
  return useQuery<IncidentTimeline>({
    queryKey: managementKeys.timeline(incidentId),
    queryFn: ({ signal }) => ManagementService.getTimeline(incidentId, signal),
    enabled: Boolean(incidentId),
    refetchInterval: env.pollLog,
    staleTime: env.pollLog / 2,
  });
}

function useUnits() {
  return useQuery<Unit[]>({
    queryKey: managementKeys.units(),
    queryFn: ({ signal }) => ManagementService.listUnits(false, signal),
    refetchInterval: env.pollResources,
    staleTime: env.pollResources / 2,
  });
}

export function useStatusCatalog() {
  return useQuery<UnitStatusOption[]>({
    queryKey: managementKeys.statusCatalog(),
    queryFn: ({ signal }) => ManagementService.statusCatalog(signal),
    staleTime: 5 * 60_000,
  });
}

/** Assigned resources composed from the incident and live unit metadata. */
export function useAssignedResources(incidentId: string): {
  resources: AssignedResource[];
  isLoading: boolean;
  isError: boolean;
} {
  const incident = useIncident(incidentId);
  const units = useUnits();

  const resources = useMemo(
    () =>
      incident.data
        ? composeAssignedResources(incident.data, units.data ?? [])
        : [],
    [incident.data, units.data],
  );

  return {
    resources,
    isLoading: incident.isLoading || units.isLoading,
    isError: incident.isError,
  };
}
