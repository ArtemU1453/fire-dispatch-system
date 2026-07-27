/**
 * IncidentService — thin, typed wrapper around the incidents REST API.
 * All data flows through the shared `request()` helper (auth, refresh, retry,
 * error normalization are handled by the axios interceptors).
 */
import { request } from "@/api/client";
import { endpoints } from "./endpoints";
import type {
  AssignUnitInput,
  Incident,
  IncidentStatus,
  IncidentSummary,
  IncidentTimeline,
} from "../types";

export const IncidentService = {
  listActive(limit = 100, signal?: AbortSignal): Promise<IncidentSummary[]> {
    return request<IncidentSummary[]>({
      url: endpoints.activeIncidents,
      method: "GET",
      params: { limit },
      signal,
    });
  },

  list(limit = 100, offset = 0, signal?: AbortSignal): Promise<IncidentSummary[]> {
    return request<IncidentSummary[]>({
      url: endpoints.incidents,
      method: "GET",
      params: { limit, offset },
      signal,
    });
  },

  get(id: string, signal?: AbortSignal): Promise<Incident> {
    return request<Incident>({ url: endpoints.incident(id), method: "GET", signal });
  },

  timeline(id: string, signal?: AbortSignal): Promise<IncidentTimeline> {
    return request<IncidentTimeline>({
      url: endpoints.incidentTimeline(id),
      method: "GET",
      signal,
    });
  },

  changeStatus(
    id: string,
    status: IncidentStatus,
    note?: string,
    actorName?: string,
  ): Promise<{ id: string; status: IncidentStatus; changed_at: string }> {
    return request({
      url: endpoints.incidentStatus(id),
      method: "PATCH",
      data: { status, note, actor_name: actorName },
    });
  },

  assignUnits(
    id: string,
    units: AssignUnitInput[],
    actorName?: string,
  ): Promise<Incident> {
    return request<Incident>({
      url: endpoints.incidentUnits(id),
      method: "POST",
      data: { units, actor_name: actorName },
    });
  },

  addComment(id: string, text: string, authorName?: string): Promise<unknown> {
    return request({
      url: endpoints.incidentComments(id),
      method: "POST",
      data: { text, author_name: authorName },
    });
  },
};

export type IncidentServiceType = typeof IncidentService;
