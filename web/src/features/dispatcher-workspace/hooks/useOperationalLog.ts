/**
 * useOperationalLog — recent operational events.
 *
 * Seeds from `LogService.recent()` and is kept live by the socket layer, which
 * prepends `log.appended` events into this same query cache (see
 * `useDispatcherSocket`). Polling is the fallback when the socket is down.
 */
import { useQuery } from "@tanstack/react-query";
import { env } from "@/lib/env";
import { LogService } from "../api";
import { dispatcherKeys } from "./queryKeys";
import type { LogEvent } from "../types";

export function useOperationalLog() {
  return useQuery<LogEvent[]>({
    queryKey: dispatcherKeys.log(),
    queryFn: ({ signal }) => LogService.recent(150, signal),
    refetchInterval: env.pollLog,
    staleTime: env.pollLog / 2,
  });
}
