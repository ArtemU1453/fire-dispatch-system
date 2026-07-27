/**
 * RegistrationService — persists the incident and hands it to the Dispatch
 * Engine (Step 7). Confirmation is two real backend calls: create the incident,
 * then assign the chosen units. Nothing is mocked; no backend logic is
 * re-implemented here.
 */
import { request } from "@/api/client";
import { endpoints } from "./endpoints";
import type {
  IncidentCategory,
  IncidentPriority,
  IncidentSource,
} from "../types";

export interface CreateIncidentInput {
  incidentTypeId: string;
  category: IncidentCategory;
  source: IncidentSource;
  priority: IncidentPriority;
  description?: string | null;
  address?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  dangerLevel?: string | null;
  objectType?: string | null;
  reporterName?: string | null;
  reporterContact?: string | null;
  actorName?: string | null;
}

export interface CreatedIncident {
  id: string;
  number: string;
  status: string;
}

export interface AssignUnitInput {
  resource_id: string;
  role?: string;
  note?: string;
}

export const RegistrationService = {
  /** Create the incident card (POST /incidents). */
  async createIncident(
    input: CreateIncidentInput,
    signal?: AbortSignal,
  ): Promise<CreatedIncident> {
    const res = await request<CreatedIncident>({
      url: endpoints.incidents,
      method: "POST",
      data: {
        incident_type_id: input.incidentTypeId,
        category: input.category,
        source: input.source,
        priority: input.priority,
        description: input.description ?? undefined,
        address: input.address ?? undefined,
        latitude: input.latitude ?? undefined,
        longitude: input.longitude ?? undefined,
        danger_level: input.dangerLevel ?? undefined,
        object_type: input.objectType ?? undefined,
        reporter_name: input.reporterName ?? undefined,
        reporter_contact: input.reporterContact ?? undefined,
        actor_name: input.actorName ?? undefined,
      },
      signal,
    });
    return res;
  },

  /** Assign the confirmed units to the incident (POST /incidents/{id}/units). */
  async assignUnits(
    incidentId: string,
    units: AssignUnitInput[],
    actorName?: string,
    signal?: AbortSignal,
  ): Promise<void> {
    await request({
      url: endpoints.incidentUnits(incidentId),
      method: "POST",
      data: { units, actor_name: actorName },
      signal,
    });
  },
};

export type RegistrationServiceType = typeof RegistrationService;
