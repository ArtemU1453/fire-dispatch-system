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
} as const;
