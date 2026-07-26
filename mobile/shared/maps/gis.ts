// Maps client (Stage 19 §Карты).
//
// Uses the EXISTING backend GIS API — the apps do not implement their own map or
// geocoding. This thin client geocodes/reverse-geocodes via the server; the UI
// layer renders tiles with a platform map component fed by these coordinates.

import type { FetchLike } from "../api/client.js";

export interface GeoPoint {
  lat: number;
  lon: number;
  label?: string;
}

export class GisClient {
  private baseUrl: string;
  private fetchImpl: FetchLike;

  constructor(baseUrl: string, fetchImpl?: FetchLike) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.fetchImpl = fetchImpl ?? (globalThis.fetch as unknown as FetchLike);
  }

  async reverse(lat: number, lon: number): Promise<string | null> {
    const res = await this.fetchImpl(
      `${this.baseUrl}/api/v1/gis/reverse?lat=${lat}&lon=${lon}`,
    );
    if (!res.ok) return null;
    const data = (await res.json()) as { address?: string } | null;
    return data?.address ?? null;
  }
}
