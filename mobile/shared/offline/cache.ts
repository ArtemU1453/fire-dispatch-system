// Local read cache (Stage 19 §Offline).
//
// Caches the last server responses so the apps show data instantly on launch
// and keep working with the last-known state while offline. TTL-bounded and
// persisted via the StorageAdapter. Purely a cache — the server remains the
// source of truth.

import type { StorageAdapter } from "./storage.js";

interface Entry<T> {
  value: T;
  expiresAt: number;
}

export class TtlCache {
  constructor(
    private storage: StorageAdapter,
    private ttlMs = 5 * 60 * 1000,
    private now: () => number = () => Date.now(),
  ) {}

  private key(k: string): string {
    return `mobile.cache.${k}`;
  }

  set<T>(key: string, value: T): void {
    const entry: Entry<T> = { value, expiresAt: this.now() + this.ttlMs };
    this.storage.set(this.key(key), JSON.stringify(entry));
  }

  // Returns the cached value if present and unexpired, else null. `stale` lets
  // the app fall back to expired data while offline.
  get<T>(key: string, opts: { stale?: boolean } = {}): T | null {
    const raw = this.storage.get(this.key(key));
    if (!raw) return null;
    const entry = JSON.parse(raw) as Entry<T>;
    if (!opts.stale && this.now() > entry.expiresAt) return null;
    return entry.value;
  }

  remove(key: string): void {
    this.storage.remove(this.key(key));
  }
}
