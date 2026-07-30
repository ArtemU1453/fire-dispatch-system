/**
 * ManagementService — the operational actions that extend the existing
 * dispatcher services (Stage 2). Read paths (get incident, timeline, units,
 * status overview, unit location, assign, add comment, change incident status)
 * are reused from `@/features/dispatcher-workspace/api`; only the genuinely new
 * write operations live here.
 */
import { request } from "@/api/client";
import {
  IncidentService,
  ResourceService,
} from "@/features/dispatcher-workspace/api";
import { endpoints } from "./endpoints";
import type { Incident, UnitStatusOption } from "../types";

export interface IncidentPatch {
  priority?: string;
  danger_level?: string;
  category?: string;
  description?: string;
  actor_name?: string;
}

interface StatusRefDto {
  id: string;
  code: string;
  name: string;
  color: string | null;
  is_available_for_dispatch: boolean;
}
interface StatusOverviewDto {
  status: StatusRefDto;
  resource_count: number;
}

export const ManagementService = {
  // --- reused read paths (existing services) ------------------------------
  getIncident: IncidentService.get,
  getTimeline: IncidentService.timeline,
  changeIncidentStatus: IncidentService.changeStatus,
  assignUnits: IncidentService.assignUnits,
  addComment: IncidentService.addComment,
  listUnits: ResourceService.listUnits,
  unitLocation: ResourceService.unitLocation,

  // --- new write operations -----------------------------------------------
  /** Partial update of the incident card (PUT accepts optional fields). */
  updateIncident(id: string, patch: IncidentPatch): Promise<Incident> {
    return request<Incident>({
      url: endpoints.incident(id),
      method: "PUT",
      data: patch,
    });
  },

  /** Change a unit's availability status (lifecycle). */
  changeUnitStatus(
    unitId: string,
    statusCode: string,
    incidentId?: string,
    actorName?: string,
  ): Promise<unknown> {
    return request({
      url: endpoints.unitStatus(unitId),
      method: "PATCH",
      data: { status_code: statusCode, incident_id: incidentId, actor_name: actorName },
    });
  },

  /** Release / cancel a unit's dispatch (return from the incident). */
  releaseUnit(unitId: string, actorName?: string): Promise<unknown> {
    return request({
      url: endpoints.unitReturn(unitId),
      method: "POST",
      params: actorName ? { actor_name: actorName } : undefined,
    });
  },

  /** The availability-status catalog (deduped from the status overview). */
  async statusCatalog(signal?: AbortSignal): Promise<UnitStatusOption[]> {
    const rows = await request<StatusOverviewDto[]>({
      url: endpoints.resourceStatus,
      method: "GET",
      signal,
    });
    const seen = new Map<string, UnitStatusOption>();
    for (const row of rows) {
      if (!seen.has(row.status.code)) {
        seen.set(row.status.code, {
          code: row.status.code,
          name: row.status.name,
          color: row.status.color,
          isAvailableForDispatch: row.status.is_available_for_dispatch,
        });
      }
    }
    return [...seen.values()];
  },
};

export type ManagementServiceType = typeof ManagementService;
