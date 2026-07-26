// Offline outbound queue (Stage 19 §Offline).
//
// Field actions (status changes, messages) are enqueued locally with a unique
// idempotency key and replayed via the backend /sync endpoint when connectivity
// returns. Because each op carries a stable op_id, replaying after a flaky
// connection never double-applies (the server dedupes). Persisted through the
// StorageAdapter so the queue survives app restarts.

import type { ApiClient } from "../api/client.js";
import type { SyncOperation, SyncResult } from "../api/types.js";
import type { StorageAdapter } from "./storage.js";

const KEY = "mobile.offline.queue";

let counter = 0;
function makeOpId(): string {
  counter += 1;
  return `${Date.now().toString(36)}-${counter.toString(36)}-${Math.random()
    .toString(36)
    .slice(2, 8)}`;
}

export class OfflineQueue {
  constructor(
    private client: ApiClient,
    private storage: StorageAdapter,
  ) {}

  private load(): SyncOperation[] {
    const raw = this.storage.get(KEY);
    return raw ? (JSON.parse(raw) as SyncOperation[]) : [];
  }

  private save(ops: SyncOperation[]): void {
    this.storage.set(KEY, JSON.stringify(ops));
  }

  get pending(): SyncOperation[] {
    return this.load();
  }

  enqueue(type: SyncOperation["type"], payload: Record<string, unknown>): string {
    const ops = this.load();
    const op: SyncOperation = { op_id: makeOpId(), type, payload };
    ops.push(op);
    this.save(ops);
    return op.op_id;
  }

  // Attempt to flush the queue. On success, applied/duplicate ops are dropped;
  // ops that errored transiently remain for the next flush. Throws on network
  // failure so the caller keeps the queue for later.
  async flush(): Promise<SyncResult[]> {
    const ops = this.load();
    if (ops.length === 0) return [];
    const { results } = await this.client.sync(ops);
    const settled = new Set(
      results.filter((r) => r.applied || r.duplicate).map((r) => r.op_id),
    );
    this.save(ops.filter((o) => !settled.has(o.op_id)));
    return results;
  }
}
