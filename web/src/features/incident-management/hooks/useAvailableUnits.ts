/**
 * Available units for assignment (dispatchable) — reuses the unit list query.
 */
import { useQuery } from "@tanstack/react-query";
import { env } from "@/lib/env";
import { ManagementService } from "../api";
import { managementKeys } from "./keys";
import type { Unit } from "@/features/dispatcher-workspace/types/resource";

export function useAvailableUnits(excludeIds: string[] = []) {
  const query = useQuery<Unit[]>({
    queryKey: managementKeys.units(),
    queryFn: ({ signal }) => ManagementService.listUnits(false, signal),
    refetchInterval: env.pollResources,
    staleTime: env.pollResources / 2,
  });
  const exclude = new Set(excludeIds);
  const available = (query.data ?? []).filter(
    (u) => u.is_available && !exclude.has(u.id),
  );
  return { ...query, available };
}
