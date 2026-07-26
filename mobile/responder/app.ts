// Responder app controller (Stage 19).
//
// Field units: shows the dispatch card and route, reports status changes and
// sends short messages. Status changes and messages go through the offline queue
// so they survive a bad connection and are replayed idempotently on reconnect.
// The server validates every status transition — the app never decides.

import { ApiClient } from "../shared/api/client.js";
import type { Dispatch, ResponderStatus, Route } from "../shared/api/types.js";
import { TtlCache } from "../shared/offline/cache.js";
import { OfflineQueue } from "../shared/offline/queue.js";
import type { StorageAdapter } from "../shared/offline/storage.js";

export class ResponderApp {
  private api: ApiClient;
  private cache: TtlCache;
  private queue: OfflineQueue;

  constructor(
    baseUrl: string,
    private unitId: string,
    storage: StorageAdapter,
    opts: { getToken?: () => string | null } = {},
  ) {
    this.api = new ApiClient({ baseUrl, getToken: opts.getToken });
    this.cache = new TtlCache(storage);
    this.queue = new OfflineQueue(this.api, storage);
  }

  async loadDispatch(): Promise<Dispatch> {
    try {
      const card = await this.api.dispatch(this.unitId);
      this.cache.set("dispatch", card);
      return card;
    } catch (err) {
      const cached = this.cache.get<Dispatch>("dispatch", { stale: true });
      if (cached) return cached;
      throw err;
    }
  }

  async loadRoute(): Promise<Route> {
    try {
      const route = await this.api.route(this.unitId);
      this.cache.set("route", route);
      return route;
    } catch (err) {
      const cached = this.cache.get<Route>("route", { stale: true });
      if (cached) return cached;
      throw err;
    }
  }

  // Report a status change. Queued locally first (works offline), then flushed.
  async reportStatus(status: ResponderStatus): Promise<void> {
    this.queue.enqueue("status", { unit_id: this.unitId, status });
    await this.trySync();
  }

  async sendMessage(text: string, incidentId?: string): Promise<void> {
    this.queue.enqueue("message", {
      unit_id: this.unitId,
      text,
      incident_id: incidentId ?? null,
    });
    await this.trySync();
  }

  // Flush the outbound queue; swallow network errors so the queue is retried.
  async trySync(): Promise<boolean> {
    try {
      await this.queue.flush();
      return true;
    } catch {
      return false;
    }
  }

  get pendingCount(): number {
    return this.queue.pending.length;
  }
}
