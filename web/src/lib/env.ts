/**
 * Centralised environment configuration. Nothing in the app hard-codes URLs —
 * everything is read from Vite env vars (see .env.example), with safe defaults.
 */
export const env = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? "/api/v1",
  apiTimeout: Number(import.meta.env.VITE_API_TIMEOUT ?? 15000),
  authLoginPath: import.meta.env.VITE_AUTH_LOGIN_PATH ?? "/admin/auth/login",
  authRefreshPath: import.meta.env.VITE_AUTH_REFRESH_PATH ?? "/admin/auth/refresh",
  authMePath: import.meta.env.VITE_AUTH_ME_PATH ?? "/admin/auth/me",
  idleTimeout: Number(import.meta.env.VITE_IDLE_TIMEOUT ?? 30 * 60 * 1000),

  /**
   * Real-time channel for the dispatcher workspace. When left empty the URL is
   * derived from the current origin (ws[s]://host/ws/dispatcher), so nothing is
   * hard-coded. The socket degrades gracefully: if it never connects, the
   * workspace keeps its data fresh through TanStack Query polling.
   */
  wsUrl: import.meta.env.VITE_WS_URL ?? "",
  wsDispatcherPath: import.meta.env.VITE_WS_DISPATCHER_PATH ?? "/ws/dispatcher",

  /** Polling fallbacks (ms) — used when the socket is not connected. */
  pollIncidents: Number(import.meta.env.VITE_POLL_INCIDENTS ?? 15000),
  pollResources: Number(import.meta.env.VITE_POLL_RESOURCES ?? 20000),
  pollStats: Number(import.meta.env.VITE_POLL_STATS ?? 15000),
  pollLog: Number(import.meta.env.VITE_POLL_LOG ?? 12000),
} as const;
