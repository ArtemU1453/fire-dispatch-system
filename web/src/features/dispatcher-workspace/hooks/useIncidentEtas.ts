/**
 * useIncidentEtas — best-effort ETA for each unit assigned to an incident.
 *
 * For every dispatched unit we resolve its live position and estimate the time
 * of arrival to the incident via the routing API. Each lookup is an independent,
 * cached query (via `useQueries`); a failure yields `null` for that unit and
 * never breaks the panel. Returns a map of resource_id → eta seconds.
 */
import { useMemo } from "react";
import { useQueries } from "@tanstack/react-query";
import { MapService, ResourceService } from "../api";
import { isValidCoord } from "../utils/geo";
import type { Incident } from "../types";

export function useIncidentEtas(incident: Incident | undefined): {
  etas: Record<string, number | null>;
  isLoading: boolean;
} {
  const hasCoords =
    !!incident && isValidCoord(incident.latitude, incident.longitude);
  const dispatches = incident?.dispatches ?? [];

  const results = useQueries({
    queries: dispatches.map((d) => ({
      queryKey: ["dispatcher", "eta", incident?.id, d.resource_id],
      enabled: hasCoords,
      staleTime: 30_000,
      queryFn: async ({ signal }: { signal?: AbortSignal }): Promise<number | null> => {
        const pos = await ResourceService.unitLocation(d.resource_id, signal).catch(
          () => null,
        );
        if (!pos || !isValidCoord(pos.latitude, pos.longitude)) return null;
        const eta = await MapService.estimateEta(
          { latitude: pos.latitude, longitude: pos.longitude },
          {
            latitude: incident!.latitude as number,
            longitude: incident!.longitude as number,
          },
          signal,
        );
        return eta ? eta.eta_seconds : null;
      },
    })),
  });

  return useMemo(() => {
    const etas: Record<string, number | null> = {};
    dispatches.forEach((d, i) => {
      etas[d.resource_id] = (results[i]?.data as number | null | undefined) ?? null;
    });
    return { etas, isLoading: results.some((r) => r.isLoading) };
    // results identity changes each render; depend on their data snapshot.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [incident?.id, JSON.stringify(results.map((r) => r.data)), dispatches.length]);
}
