import { useQueries, useQuery } from '@tanstack/react-query';

import { buildRoute, estimateEta, getResource } from '../api/endpoints';
import type { LatLon } from '../api/endpoints';
import type { ETAResponse, ResourceSearchItem, RouteResponse } from '../types/api';

/** Resource details (with coordinates) for a set of recommended unit ids. */
export function useUnitDetails(resourceIds: string[]) {
  const queries = useQueries({
    queries: resourceIds.map((id) => ({
      queryKey: ['resource', id],
      queryFn: () => getResource(id),
      staleTime: 60_000,
    })),
  });
  const byId = new Map<string, ResourceSearchItem>();
  queries.forEach((q) => {
    if (q.data) byId.set(q.data.id, q.data);
  });
  return { byId, isLoading: queries.some((q) => q.isLoading) };
}

/** ETA from the incident to each recommended unit (parallel queries). */
export function useUnitEtas(origin: LatLon | null, units: ResourceSearchItem[]) {
  const queries = useQueries({
    queries: units
      .filter((u) => u.latitude != null && u.longitude != null && origin)
      .map((u) => ({
        queryKey: ['eta', origin?.lat, origin?.lon, u.id],
        queryFn: () =>
          estimateEta(origin as LatLon, {
            lat: u.latitude as number,
            lon: u.longitude as number,
          }),
        staleTime: 60_000,
      })),
  });
  const byId = new Map<string, ETAResponse>();
  const ids = units.filter((u) => u.latitude != null && u.longitude != null);
  queries.forEach((q, index) => {
    if (q.data && ids[index]) byId.set(ids[index].id, q.data);
  });
  return byId;
}

/** A full route between the incident and a focused unit (for the map). */
export function useRouteTo(origin: LatLon | null, destination: LatLon | null) {
  return useQuery<RouteResponse>({
    queryKey: ['route', origin?.lat, origin?.lon, destination?.lat, destination?.lon],
    queryFn: () => buildRoute(origin as LatLon, destination as LatLon),
    enabled: Boolean(origin && destination),
    staleTime: 60_000,
  });
}
