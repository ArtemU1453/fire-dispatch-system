import axios, {
  AxiosError,
  type AxiosInstance,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from "axios";
import { env } from "@/lib/env";
import type { ApiErrorShape } from "@/types/api";
import { useAuthStore } from "@/store/auth.store";
import { useUserStore } from "@/store/user.store";

type RetryConfig = InternalAxiosRequestConfig & { _retry?: boolean; _retryCount?: number };

const MAX_RETRIES = 2;

/** Raw instance without interceptors — used for the token refresh call itself. */
const raw: AxiosInstance = axios.create({
  baseURL: env.apiBaseUrl,
  timeout: env.apiTimeout,
});

/** Main API client used across the app. */
export const apiClient: AxiosInstance = axios.create({
  baseURL: env.apiBaseUrl,
  timeout: env.apiTimeout,
  headers: { "Content-Type": "application/json" },
  // CSRF-ready: the backend can require these; harmless when it doesn't.
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "X-CSRF-Token",
});

// ---- Request: attach the access token ------------------------------------
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.set("Authorization", `Bearer ${token}`);
  return config;
});

// ---- Refresh coordination --------------------------------------------------
let refreshing: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const { refreshToken, setTokens } = useAuthStore.getState();
  if (!refreshToken) return null;
  try {
    const { data } = await raw.post(env.authRefreshPath, { refresh_token: refreshToken });
    const accessToken: string = data.access_token ?? data.accessToken;
    const newRefresh: string = data.refresh_token ?? data.refreshToken ?? refreshToken;
    setTokens({ accessToken, refreshToken: newRefresh });
    return accessToken;
  } catch {
    return null;
  }
}

function forceLogout() {
  useAuthStore.getState().clearTokens();
  useUserStore.getState().clearUser();
}

function normalizeError(error: AxiosError): ApiErrorShape {
  const status = error.response?.status ?? 0;
  const data = error.response?.data as Record<string, unknown> | undefined;
  const message =
    (data?.detail as string) ||
    (data?.message as string) ||
    error.message ||
    "Неизвестная ошибка";
  return {
    status,
    code: status === 0 ? "NETWORK" : String((data?.code as string) ?? status),
    message: status === 0 ? "Нет соединения с сервером" : message,
    details: data,
  };
}

// ---- Response: refresh on 401, retry on network/5xx, normalize errors ------
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetryConfig | undefined;
    const status = error.response?.status;

    // 401 → try a single refresh, then retry the original request once.
    if (status === 401 && config && !config._retry) {
      config._retry = true;
      refreshing = refreshing ?? refreshAccessToken();
      const newToken = await refreshing;
      refreshing = null;
      if (newToken) {
        config.headers.set("Authorization", `Bearer ${newToken}`);
        return apiClient(config);
      }
      forceLogout();
      return Promise.reject(normalizeError(error));
    }

    // Retry idempotent GETs on network error / 5xx with linear backoff.
    const retriable =
      config &&
      (config.method ?? "get").toLowerCase() === "get" &&
      (status === undefined || status >= 500);
    if (retriable && config) {
      config._retryCount = (config._retryCount ?? 0) + 1;
      if (config._retryCount <= MAX_RETRIES) {
        await new Promise((r) => setTimeout(r, 300 * config._retryCount!));
        return apiClient(config);
      }
    }

    return Promise.reject(normalizeError(error));
  },
);

/** Typed helper around the client. */
export async function request<T>(config: AxiosRequestConfig): Promise<T> {
  const { data } = await apiClient.request<T>(config);
  return data;
}

export { raw as rawClient };
