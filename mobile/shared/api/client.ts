// Backend API client (Stage 19).
//
// The single gateway to the server. The apps contain NO business logic — they
// only call these endpoints and render results. Uses injectable `fetch` (so it
// is testable) and a token provider for auth. All traffic is HTTPS in
// production; requests are minimal (no client-side polling loops here).

import type {
  Dashboard,
  Dispatch,
  Incident,
  Resource,
  Route,
  ResponderStatus,
  SyncOperation,
  SyncResult,
} from "./types.js";

export type FetchLike = (
  url: string,
  init?: {
    method?: string;
    headers?: Record<string, string>;
    body?: string;
  },
) => Promise<{ ok: boolean; status: number; json: () => Promise<unknown> }>;

export interface ApiOptions {
  baseUrl: string;
  fetchImpl?: FetchLike;
  getToken?: () => string | null;
  onUnauthorized?: () => void;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

export class ApiClient {
  private baseUrl: string;
  private fetchImpl: FetchLike;
  private getToken: () => string | null;
  private onUnauthorized?: () => void;

  constructor(opts: ApiOptions) {
    this.baseUrl = opts.baseUrl.replace(/\/$/, "");
    this.fetchImpl = opts.fetchImpl ?? (globalThis.fetch as unknown as FetchLike);
    this.getToken = opts.getToken ?? (() => null);
    this.onUnauthorized = opts.onUnauthorized;
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
  ): Promise<T> {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    const token = this.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await this.fetchImpl(`${this.baseUrl}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (res.status === 401) {
      this.onUnauthorized?.();
      throw new ApiError(401, "unauthorized");
    }
    const data = (await res.json().catch(() => null)) as T;
    if (!res.ok) {
      throw new ApiError(res.status, `request failed: ${res.status}`);
    }
    return data;
  }

  // --- Commander ---
  dashboard(): Promise<Dashboard> {
    return this.request("GET", "/api/v1/mobile/commander/dashboard");
  }
  incidents(activeOnly = true): Promise<Incident[]> {
    return this.request(
      "GET",
      `/api/v1/mobile/commander/incidents?active_only=${activeOnly}`,
    );
  }
  resources(): Promise<Resource[]> {
    return this.request("GET", "/api/v1/mobile/commander/resources");
  }

  // --- Responder ---
  dispatch(unitId: string): Promise<Dispatch> {
    return this.request(
      "GET",
      `/api/v1/mobile/responder/dispatch?unit_id=${encodeURIComponent(unitId)}`,
    );
  }
  route(unitId: string): Promise<Route> {
    return this.request(
      "GET",
      `/api/v1/mobile/responder/route?unit_id=${encodeURIComponent(unitId)}`,
    );
  }
  setStatus(unitId: string, status: ResponderStatus): Promise<unknown> {
    return this.request("PATCH", "/api/v1/mobile/responder/status", {
      unit_id: unitId,
      status,
    });
  }
  sendMessage(
    unitId: string,
    text: string,
    incidentId?: string,
  ): Promise<unknown> {
    return this.request("POST", "/api/v1/mobile/responder/message", {
      unit_id: unitId,
      text,
      incident_id: incidentId ?? null,
    });
  }

  // --- Devices / offline sync ---
  registerDevice(
    token: string,
    userId: string,
    app: string,
    platform: string,
  ): Promise<unknown> {
    return this.request("POST", "/api/v1/mobile/devices", {
      token,
      user_id: userId,
      app,
      platform,
    });
  }
  sync(operations: SyncOperation[]): Promise<{ results: SyncResult[] }> {
    return this.request("POST", "/api/v1/mobile/sync", { operations });
  }
}
