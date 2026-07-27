/**
 * ResourceService — units, vehicles, positions and status overview.
 */
import { request } from "@/api/client";
import { endpoints } from "./endpoints";
import type { Position, StatusOverviewItem, Unit, Vehicle } from "../types";

export const ResourceService = {
  listUnits(activeOnly = false, signal?: AbortSignal): Promise<Unit[]> {
    return request<Unit[]>({
      url: endpoints.units,
      method: "GET",
      params: { active: activeOnly },
      signal,
    });
  },

  getUnit(id: string, signal?: AbortSignal): Promise<Unit> {
    return request<Unit>({ url: endpoints.unit(id), method: "GET", signal });
  },

  /** Current location of a unit; may be null if the unit has no tracked vehicle. */
  unitLocation(id: string, signal?: AbortSignal): Promise<Position | null> {
    return request<Position | null>({
      url: endpoints.unitLocation(id),
      method: "GET",
      signal,
    });
  },

  listVehicles(signal?: AbortSignal): Promise<Vehicle[]> {
    return request<Vehicle[]>({ url: endpoints.vehicles, method: "GET", signal });
  },

  statusOverview(signal?: AbortSignal): Promise<StatusOverviewItem[]> {
    return request<StatusOverviewItem[]>({
      url: endpoints.resourcesStatus,
      method: "GET",
      signal,
    });
  },
};

export type ResourceServiceType = typeof ResourceService;
