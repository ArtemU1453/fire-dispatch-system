/**
 * Header KPI hook — active incidents, free/busy units, average ETA.
 */
import { useQuery } from "@tanstack/react-query";
import { env } from "@/lib/env";
import { StatisticsService } from "../api";
import { dispatcherKeys } from "./queryKeys";

export function useWorkspaceStats() {
  return useQuery({
    queryKey: dispatcherKeys.stats(),
    queryFn: ({ signal }) => StatisticsService.getWorkspaceStats(signal),
    refetchInterval: env.pollStats,
    staleTime: env.pollStats / 2,
  });
}
