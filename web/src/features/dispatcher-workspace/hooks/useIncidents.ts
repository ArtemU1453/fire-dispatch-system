/**
 * Incident data hooks (active list, filtered selector, details, timeline).
 */
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { env } from "@/lib/env";
import { IncidentService } from "../api";
import { dispatcherKeys } from "./queryKeys";
import { useDispatcherStore } from "../store/dispatcher.store";
import { filterAndSortIncidents } from "../utils/filter";
import type { IncidentSummary } from "../types";

/** Raw active-incident list (server truth). */
export function useActiveIncidents() {
  return useQuery({
    queryKey: dispatcherKeys.activeIncidents(),
    queryFn: ({ signal }) => IncidentService.listActive(500, signal),
    refetchInterval: env.pollIncidents,
    staleTime: env.pollIncidents / 2,
  });
}

/** Active incidents with the store's search / filter / sort applied. */
export function useFilteredIncidents(): {
  incidents: IncidentSummary[];
  total: number;
  isLoading: boolean;
  isError: boolean;
  refetch: () => void;
} {
  const query = useActiveIncidents();
  const filters = useDispatcherStore((s) => s.filters);
  const incidents = useMemo(
    () => filterAndSortIncidents(query.data ?? [], filters),
    [query.data, filters],
  );
  return {
    incidents,
    total: query.data?.length ?? 0,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}

/** Full incident detail. */
export function useIncidentDetails(incidentId: string | null) {
  return useQuery({
    queryKey: incidentId ? dispatcherKeys.incident(incidentId) : dispatcherKeys.incident("none"),
    queryFn: ({ signal }) => IncidentService.get(incidentId as string, signal),
    enabled: Boolean(incidentId),
    staleTime: 10_000,
  });
}

/** Incident timeline (history) for the details panel. */
export function useIncidentTimeline(incidentId: string | null) {
  return useQuery({
    queryKey: incidentId
      ? dispatcherKeys.incidentTimeline(incidentId)
      : dispatcherKeys.incidentTimeline("none"),
    queryFn: ({ signal }) => IncidentService.timeline(incidentId as string, signal),
    enabled: Boolean(incidentId),
    staleTime: 10_000,
  });
}
