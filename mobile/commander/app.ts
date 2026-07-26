// Commander app controller (Stage 19).
//
// Command staff: shows the dashboard, incidents, resource load, map and
// critical notifications, and lets authorised users add notes/comments. It is a
// thin controller — it calls the SDK and caches for offline; it makes NO
// operational decisions (the server does). UI (light/dark theme, large one-hand
// controls, phone/tablet layouts) is built on top of this controller.

import { ApiClient } from "../shared/api/client.js";
import type { Dashboard } from "../shared/api/types.js";
import { TtlCache } from "../shared/offline/cache.js";
import type { StorageAdapter } from "../shared/offline/storage.js";
import { PushClient, type PushTransport } from "../shared/notifications/push.js";

export class CommanderApp {
  private api: ApiClient;
  private cache: TtlCache;
  private push?: PushClient;

  constructor(
    baseUrl: string,
    storage: StorageAdapter,
    opts: { getToken?: () => string | null; transport?: PushTransport } = {},
  ) {
    this.api = new ApiClient({ baseUrl, getToken: opts.getToken });
    this.cache = new TtlCache(storage);
    if (opts.transport) this.push = new PushClient(this.api, opts.transport);
  }

  // Load the dashboard; fall back to cached (even stale) data when offline.
  async loadDashboard(): Promise<Dashboard> {
    try {
      const data = await this.api.dashboard();
      this.cache.set("dashboard", data);
      return data;
    } catch (err) {
      const cached = this.cache.get<Dashboard>("dashboard", { stale: true });
      if (cached) return cached;
      throw err;
    }
  }

  async subscribe(userId: string, platform: string): Promise<void> {
    await this.push?.register(userId, "commander", platform);
  }

  onCritical(handler: (title: string, body: string) => void): void {
    this.push?.on("critical", (m) => handler(m.title, m.body));
    this.push?.on("new_incident", (m) => handler(m.title, m.body));
  }
}
