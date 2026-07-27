/**
 * CatalogService — reference data needed by the form (incident types).
 */
import { request } from "@/api/client";
import { endpoints } from "./endpoints";
import type { IncidentTypeOption } from "../types";

interface DirectoryItemDto {
  id: string;
  code: string;
  name: string;
  is_deleted: boolean;
}

export const CatalogService = {
  async incidentTypes(signal?: AbortSignal): Promise<IncidentTypeOption[]> {
    const rows = await request<DirectoryItemDto[]>({
      url: endpoints.incidentTypes,
      method: "GET",
      signal,
    });
    return rows
      .filter((r) => !r.is_deleted)
      .map((r) => ({ id: r.id, code: r.code, name: r.name }));
  },
};

export type CatalogServiceType = typeof CatalogService;
