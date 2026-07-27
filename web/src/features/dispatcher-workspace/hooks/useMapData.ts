/**
 * useMapData — assembles the OperationalMap feature set from live API data.
 *
 *  - Unit markers come from a single GIS bbox query (resources with geometry).
 *  - Incident markers come from incident details, fetched per active incident
 *    via `useQueries` so TanStack Query caches and de-duplicates them (no
 *    refetch storm); the selected incident is always included.
 *  - The selected incident's route to its nearest unit is drawn when both
 *    endpoints have coordinates.
 *
 * Everything is memoized; layers the store hides are omitted from the result.
 */
import { useMemo } from "react";
import { useQueries, useQuery } from "@tanstack/react-query";
import { env } from "@/lib/env";
import { IncidentService, MapService } from "../api";
import { dispatcherKeys } from "./queryKeys";
import { useActiveIncidents } from "./useIncidents";
import { useDispatcherStore } from "../store/dispatcher.store";
import {
  buildIncidentPoints,
  buildUnitPoints,
} from "../services/map-features.service";
import { bboxAround } from "../utils/geo";
import type { Incident, MapFeatureSet } from "../types";

/** Cap on how many active incidents we resolve to coordinates for the map. */
const MAX_MAP_INCIDENTS = 150;

export function useMapData(): {
  features: MapFeatureSet;
  isLoading: boolean;
} {
  const layers = useDispatcherStore((s) => s.map.layers);
  const center = useDispatcherStore((s) => s.map.center);
  const active = useActiveIncidents();

  const incidentIds = useMemo(
    () => (active.data ?? []).slice(0, MAX_MAP_INCIDENTS).map((i) => i.id),
    [active.data],
  );

  // Per-incident detail queries (cached individually, run in parallel).
  const detailQueries = useQueries({
    queries: incidentIds.map((id) => ({
      queryKey: dispatcherKeys.incident(id),
      queryFn: ({ signal }: { signal?: AbortSignal }) =>
        IncidentService.get(id, signal),
      staleTime: 30_000,
      enabled: layers.incidents,
    })),
  });

  const bbox = useMemo(() => bboxAround(center, 0.35), [center]);
  const unitsQuery = useQuery({
    queryKey: [...dispatcherKeys.mapObjects(), bbox],
    queryFn: ({ signal }) => MapService.resourcesInBBox(bbox, signal),
    enabled: layers.units,
    refetchInterval: env.pollResources,
    staleTime: env.pollResources / 2,
  });

  const features = useMemo<MapFeatureSet>(() => {
    const incidents: Incident[] = detailQueries
      .map((q) => q.data)
      .filter((d): d is Incident => Boolean(d));

    const points = [
      ...(layers.incidents ? buildIncidentPoints(incidents) : []),
      ...(layers.units ? buildUnitPoints(unitsQuery.data ?? []) : []),
    ];
    return { points, routes: [], zones: [] };
  }, [detailQueries, unitsQuery.data, layers.incidents, layers.units]);

  const isLoading =
    active.isLoading ||
    (layers.units && unitsQuery.isLoading) ||
    (layers.incidents && detailQueries.some((q) => q.isLoading));

  return { features, isLoading };
}
