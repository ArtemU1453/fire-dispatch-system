/**
 * AddressService — geocoding search and reverse resolution (Steps 2–3).
 */
import { request } from "@/api/client";
import { endpoints } from "./endpoints";
import type { AddressCandidate, ResolvedArea } from "../types";

interface GeocodeResultDto {
  formatted_address: string;
  normalized_address: string | null;
  latitude: number;
  longitude: number;
  accuracy: string;
  source: string;
}

interface GeocodeResponseDto {
  query: string;
  success: boolean;
  error: string | null;
  count: number;
  results: GeocodeResultDto[];
}

interface AddressComponentsDto {
  region: string | null;
  district: string | null;
  settlement: string | null;
  street: string | null;
  house_number: string | null;
  formatted_address: string | null;
}

interface ReverseResponseDto {
  success: boolean;
  error: string | null;
  address: AddressComponentsDto | null;
}

export const AddressService = {
  /** Autocomplete search — one request per (debounced) keystroke. */
  async search(
    query: string,
    limit = 7,
    signal?: AbortSignal,
  ): Promise<AddressCandidate[]> {
    const res = await request<GeocodeResponseDto>({
      url: endpoints.geocode,
      method: "GET",
      params: { q: query, limit, country_codes: "ru" },
      signal,
    });
    return res.results.map((r, i) => ({
      id: `${r.latitude.toFixed(6)},${r.longitude.toFixed(6)}:${i}`,
      formatted_address: r.formatted_address,
      normalized_address: r.normalized_address,
      latitude: r.latitude,
      longitude: r.longitude,
      accuracy: r.accuracy,
      source: r.source,
    }));
  },

  /** Reverse geocode a point to district / settlement / region components. */
  async resolveArea(
    latitude: number,
    longitude: number,
    signal?: AbortSignal,
  ): Promise<ResolvedArea | null> {
    const res = await request<ReverseResponseDto>({
      url: endpoints.reverse,
      method: "GET",
      params: { lat: latitude, lon: longitude },
      signal,
    });
    if (!res.address) return null;
    return {
      region: res.address.region,
      district: res.address.district,
      settlement: res.address.settlement,
      street: res.address.street,
      house_number: res.address.house_number,
      formatted_address: res.address.formatted_address,
    };
  },
};

export type AddressServiceType = typeof AddressService;
