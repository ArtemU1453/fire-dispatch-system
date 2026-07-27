/**
 * Resource data hooks — units list and status overview.
 */
import { useQuery } from "@tanstack/react-query";
import { env } from "@/lib/env";
import { ResourceService } from "../api";
import { dispatcherKeys } from "./queryKeys";

export function useUnits() {
  return useQuery({
    queryKey: dispatcherKeys.units(),
    queryFn: ({ signal }) => ResourceService.listUnits(false, signal),
    refetchInterval: env.pollResources,
    staleTime: env.pollResources / 2,
  });
}

export function useResourceStatus() {
  return useQuery({
    queryKey: dispatcherKeys.resourceStatus(),
    queryFn: ({ signal }) => ResourceService.statusOverview(signal),
    refetchInterval: env.pollResources,
    staleTime: env.pollResources / 2,
  });
}
