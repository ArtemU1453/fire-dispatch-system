/**
 * Best-effort ETA for the selected units, from each unit's known position
 * (nearest-resource coordinates) to the incident, via the routing API. Each
 * lookup is an independent cached query; failures yield null and never block
 * confirmation.
 */
import { useMemo } from "react";
import { useQueries } from "@tanstack/react-query";
import { MapService } from "@/features/dispatcher-workspace/api";
import { useNearestResources } from "./useRegistrationData";
import { useRegistrationStore } from "../store/registration.store";
import { isValidCoord } from "../utils";

export function useSelectedEtas(): Record<string, number | null> {
  const location = useRegistrationStore((s) => s.location);
  const selected = useRegistrationStore((s) => s.selectedUnits);
  const { data: nearest = [] } = useNearestResources();

  const coordsById = useMemo(
    () => new Map(nearest.map((u) => [u.id, u])),
    [nearest],
  );

  const results = useQueries({
    queries: selected.map((u) => {
      const pos = coordsById.get(u.resource_id);
      const enabled =
        !!location && !!pos && isValidCoord(pos.latitude, pos.longitude);
      return {
        queryKey: [
          "registration",
          "eta",
          u.resource_id,
          location?.latitude,
          location?.longitude,
        ],
        enabled,
        staleTime: 30_000,
        queryFn: async ({ signal }: { signal?: AbortSignal }): Promise<number | null> => {
          const eta = await MapService.estimateEta(
            { latitude: pos!.latitude as number, longitude: pos!.longitude as number },
            { latitude: location!.latitude, longitude: location!.longitude },
            signal,
          );
          return eta ? eta.eta_seconds : null;
        },
      };
    }),
  });

  return useMemo(() => {
    const map: Record<string, number | null> = {};
    selected.forEach((u, i) => {
      map[u.resource_id] =
        (results[i]?.data as number | null | undefined) ?? u.eta_seconds ?? null;
    });
    return map;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected, JSON.stringify(results.map((r) => r.data))]);
}
