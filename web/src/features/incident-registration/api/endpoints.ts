/**
 * REST endpoint paths for the registration workflow, relative to
 * `env.apiBaseUrl`. These map the workflow steps to the real backend contract
 * (no new backend logic is duplicated on the client).
 */
export const endpoints = {
  geocode: "/geocode", // GET ?q= — address search / autocomplete
  reverse: "/reverse", // GET ?lat=&lon= — district / municipality
  incidentTypes: "/admin/directories/incident_types", // GET — type catalog
  nearestResources: "/resources/nearest", // GET ?lat=&lon= — nearby units
  dispatchPreview: "/dispatch/preview", // POST — AI recommendation
  incidents: "/incidents", // POST — create incident
  incidentUnits: (id: string) => `/incidents/${id}/units`, // POST — assign
} as const;
