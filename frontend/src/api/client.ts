/**
 * Axios instance and error normalization.
 *
 * A single configured client is shared by every endpoint module. Backend errors
 * (network failures, 4xx/5xx, timeouts) are normalized into a small `ApiError`
 * with a user-friendly Russian message so the UI can present it consistently.
 */
import axios, { AxiosError, type AxiosInstance } from 'axios';

const baseURL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1';

export const apiClient: AxiosInstance = axios.create({
  baseURL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

export type ApiErrorKind =
  | 'network'
  | 'timeout'
  | 'unavailable'
  | 'not_found'
  | 'validation'
  | 'server'
  | 'unknown';

export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly status?: number;
  readonly detail?: string;

  constructor(message: string, kind: ApiErrorKind, status?: number, detail?: string) {
    super(message);
    this.name = 'ApiError';
    this.kind = kind;
    this.status = status;
    this.detail = detail;
  }
}

function detailFrom(data: unknown): string | undefined {
  if (data && typeof data === 'object' && 'detail' in data) {
    const d = (data as { detail: unknown }).detail;
    if (typeof d === 'string') return d;
    if (Array.isArray(d) && d.length > 0) {
      const first = d[0] as { msg?: string };
      return first?.msg;
    }
  }
  return undefined;
}

export function normalizeError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;
  const axiosError = error as AxiosError;

  if (axiosError?.code === 'ECONNABORTED') {
    return new ApiError('Превышено время ожидания ответа сервера.', 'timeout');
  }
  if (axiosError?.response) {
    const status = axiosError.response.status;
    const detail = detailFrom(axiosError.response.data);
    if (status === 404) {
      return new ApiError(detail ?? 'Данные не найдены.', 'not_found', status, detail);
    }
    if (status === 422) {
      return new ApiError(
        detail ?? 'Некорректный запрос.',
        'validation',
        status,
        detail,
      );
    }
    if (status === 503) {
      return new ApiError(
        detail ?? 'Сервис временно недоступен.',
        'unavailable',
        status,
        detail,
      );
    }
    return new ApiError(
      detail ?? `Ошибка сервера (${status}).`,
      'server',
      status,
      detail,
    );
  }
  if (axiosError?.request) {
    return new ApiError(
      'Нет связи с сервером. Проверьте подключение.',
      'network',
    );
  }
  return new ApiError('Неизвестная ошибка.', 'unknown');
}

apiClient.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(normalizeError(error)),
);
