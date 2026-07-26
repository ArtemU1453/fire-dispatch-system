// Secure token store & idle-timeout (Stage 19 §Безопасность).
//
// Holds the session token in the platform's encrypted storage (never in plain
// text), tracks activity for auto-logout after inactivity, and clears on remote
// revocation / 401. Passwords are never handled on device — only the session
// token issued by the server after authentication.

import type { StorageAdapter } from "../offline/storage.js";

const TOKEN_KEY = "mobile.session.token";
const SEEN_KEY = "mobile.session.lastSeen";

export class TokenStore {
  constructor(
    private secureStorage: StorageAdapter,
    private idleMs = 30 * 60 * 1000,
    private now: () => number = () => Date.now(),
  ) {}

  set(token: string): void {
    this.secureStorage.set(TOKEN_KEY, token);
    this.touch();
  }

  // Returns the token only if a session exists and has not idled out; otherwise
  // clears it (auto-logout) and returns null.
  get(): string | null {
    const token = this.secureStorage.get(TOKEN_KEY);
    if (!token) return null;
    if (this.isIdleExpired()) {
      this.clear();
      return null;
    }
    return token;
  }

  touch(): void {
    this.secureStorage.set(SEEN_KEY, String(this.now()));
  }

  isIdleExpired(): boolean {
    const seen = this.secureStorage.get(SEEN_KEY);
    if (!seen) return false;
    return this.now() - Number(seen) >= this.idleMs;
  }

  clear(): void {
    this.secureStorage.remove(TOKEN_KEY);
    this.secureStorage.remove(SEEN_KEY);
  }
}
