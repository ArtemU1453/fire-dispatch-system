import { useMutation } from '@tanstack/react-query';

import { geocode } from '../api/endpoints';
import type { ApiError } from '../api/client';
import { useNotificationStore } from '../store/notifications';
import type { GeocodeResponse } from '../types/api';

/** Forward geocoding as a mutation (fired when the dispatcher searches). */
export function useGeocode() {
  const notify = useNotificationStore((s) => s.notify);
  return useMutation<GeocodeResponse, ApiError, string>({
    mutationFn: (query: string) => geocode(query, 5),
    onError: (error) => notify('error', `Геокодирование: ${error.message}`),
    onSuccess: (data) => {
      if (!data.success || data.count === 0) {
        notify('warning', 'Адрес не найден. Уточните запрос.');
      }
    },
  });
}
