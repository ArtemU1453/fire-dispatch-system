/**
 * StatisticsService — the header KPIs.
 *
 * There is no single "dashboard stats" endpoint on the backend, so the figures
 * are aggregated from real resources: the active-incident list and the resource
 * status overview. This is deliberate composition of live API data — not a mock.
 */
import { IncidentService } from "./incident.service";
import { ResourceService } from "./resource.service";
import type { StatusOverviewItem, WorkspaceStats } from "../types";

function countUnits(overview: StatusOverviewItem[]): {
  free: number;
  busy: number;
} {
  let free = 0;
  let busy = 0;
  for (const item of overview) {
    if (item.status.is_available_for_dispatch) {
      free += item.resource_count;
    } else if (item.status.is_operational) {
      busy += item.resource_count;
    }
  }
  return { free, busy };
}

export const StatisticsService = {
  async getWorkspaceStats(signal?: AbortSignal): Promise<WorkspaceStats> {
    const [incidents, overview] = await Promise.all([
      IncidentService.listActive(500, signal),
      ResourceService.statusOverview(signal),
    ]);
    const { free, busy } = countUnits(overview);
    return {
      activeIncidents: incidents.length,
      freeUnits: free,
      busyUnits: busy,
      // Average ETA is derived by the details/map layer where routes exist;
      // at the aggregate level it is unknown until routes are computed.
      avgEtaSeconds: null,
    };
  },
};

export type StatisticsServiceType = typeof StatisticsService;
