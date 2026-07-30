/**
 * REST endpoint paths for operational incident management, relative to
 * `env.apiBaseUrl`. Mapped to the real backend contract (no backend logic is
 * duplicated on the client):
 *
 *   GET   /incidents/{id}                 → incident card
 *   PUT   /incidents/{id}                 → partial update (call level, …)
 *   PATCH /incidents/{id}/status          → status change / close
 *   GET   /incidents/{id}/timeline        → operational timeline
 *   POST  /incidents/{id}/units           → assign resources
 *   POST  /incidents/{id}/comments        → dispatcher message
 *   PATCH /units/{id}/status              → unit status lifecycle
 *   POST  /units/{id}/return              → release / cancel dispatch
 *   GET   /units/{id}/location            → live position (speed if available)
 *   GET   /units                          → unit metadata (enrichment)
 *   GET   /resources/status               → availability-status catalog
 */
export const endpoints = {
  incident: (id: string) => `/incidents/${id}`,
  incidentStatus: (id: string) => `/incidents/${id}/status`,
  incidentTimeline: (id: string) => `/incidents/${id}/timeline`,
  incidentUnits: (id: string) => `/incidents/${id}/units`,
  incidentComments: (id: string) => `/incidents/${id}/comments`,

  units: "/units",
  unitStatus: (unitId: string) => `/units/${unitId}/status`,
  unitReturn: (unitId: string) => `/units/${unitId}/return`,
  unitLocation: (unitId: string) => `/units/${unitId}/location`,

  resourceStatus: "/resources/status",
} as const;
