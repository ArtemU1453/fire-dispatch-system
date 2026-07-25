import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type { ApiError } from '../api/client';
import { getRecommendation, recommend } from '../api/endpoints';
import { useIncidentStore } from '../store/incident';
import { useNotificationStore } from '../store/notifications';
import type { DispatchRequest, RecommendationResponse } from '../types/api';

/** Read a persisted recommendation by incident id (server state). */
export function useRecommendationQuery(incidentId: string | null) {
  return useQuery<RecommendationResponse>({
    queryKey: ['recommendation', incidentId],
    queryFn: () => getRecommendation(incidentId as string),
    enabled: Boolean(incidentId),
  });
}

/** Request a recommendation (POST). Caches the result under its incident id. */
export function useRecommendMutation() {
  const queryClient = useQueryClient();
  const notify = useNotificationStore((s) => s.notify);
  const setIncidentId = useIncidentStore((s) => s.setIncidentId);
  const setSelectedUnits = useIncidentStore((s) => s.setSelectedUnits);

  return useMutation<
    RecommendationResponse,
    ApiError,
    { request: DispatchRequest; preview?: boolean }
  >({
    mutationFn: ({ request, preview }) => recommend(request, preview),
    onSuccess: (data, variables) => {
      const key = variables.request.incident_id ?? data.id;
      queryClient.setQueryData(['recommendation', key], data);
      setIncidentId(key);
      // Pre-select the recommended primary units.
      setSelectedUnits(data.primary_units.map((u) => u.resource_id));
      if (data.status === 'no_resources') {
        notify('warning', 'Доступных подразделений не найдено.');
      } else if (!data.sufficient) {
        notify('warning', 'Сформирован неполный состав.');
      } else {
        notify('success', 'Рекомендация сформирована.');
      }
    },
    onError: (error) => notify('error', `Рекомендация: ${error.message}`),
  });
}
