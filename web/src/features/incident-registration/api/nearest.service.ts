/**
 * NearestService — nearby resources around the incident point (Step 3 map).
 */
import { request } from "@/api/client";
import { endpoints } from "./endpoints";
import type { NearestResource } from "../types";

interface RefLabelDto {
  id: string;
  code: string | null;
  name: string | null;
}

interface NearestItemDto {
  id: string;
  code: string;
  name: string;
  latitude: number | null;
  longitude: number | null;
  distance_meters: number | null;
  resource_type: RefLabelDto | null;
  availability_status: RefLabelDto | null;
}

interface SearchResponseDto {
  total: number;
  count: number;
  items: NearestItemDto[];
}

export const NearestService = {
  async near(
    latitude: number,
    longitude: number,
    limit = 12,
    signal?: AbortSignal,
  ): Promise<NearestResource[]> {
    const res = await request<SearchResponseDto>({
      url: endpoints.nearestResources,
      method: "GET",
      params: { lat: latitude, lon: longitude, limit },
      signal,
    });
    return res.items.map((i) => ({
      id: i.id,
      code: i.code,
      name: i.name,
      latitude: i.latitude,
      longitude: i.longitude,
      distance_meters: i.distance_meters,
      resource_type: i.resource_type?.name ?? null,
      availability_status: i.availability_status?.name ?? null,
    }));
  },
};

export type NearestServiceType = typeof NearestService;
