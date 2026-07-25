import { useQuery } from '@tanstack/react-query';

import { getRule, listRules } from '../api/endpoints';
import type { IncidentTypeOption } from '../types/api';

/**
 * Derives the selectable incident types from the Rules API.
 *
 * The backend has no "list incident types" endpoint, so — without changing the
 * backend — we aggregate the incident types that have an enabled dispatch rule
 * (the ones actually dispatchable), labelling each by its rule. A manual UUID
 * entry remains available in the incident card as a fallback.
 */
export function useIncidentTypes() {
  return useQuery<IncidentTypeOption[]>({
    queryKey: ['incident-types'],
    staleTime: 5 * 60_000,
    queryFn: async () => {
      const rules = await listRules();
      const details = await Promise.all(
        rules.slice(0, 50).map((r) => getRule(r.id).catch(() => null)),
      );
      const byType = new Map<string, IncidentTypeOption>();
      details.forEach((detail) => {
        if (!detail) return;
        detail.incident_type_ids.forEach((typeId) => {
          if (!byType.has(typeId)) {
            byType.set(typeId, {
              id: typeId,
              code: detail.name,
              name: detail.name,
            });
          }
        });
      });
      return Array.from(byType.values());
    },
  });
}
