/**
 * REST endpoint paths for the dispatcher workspace, relative to
 * `env.apiBaseUrl`. Centralised so the API contract lives in one place
 * (the base URL itself is never hard-coded — it comes from the environment).
 */
export const endpoints = {
  incidents: "/incidents",
  activeIncidents: "/incidents/active",
  incident: (id: string) => `/incidents/${id}`,
  incidentTimeline: (id: string) => `/incidents/${id}/timeline`,
  incidentStatus: (id: string) => `/incidents/${id}/status`,
  incidentUnits: (id: string) => `/incidents/${id}/units`,
  incidentComments: (id: string) => `/incidents/${id}/comments`,

  units: "/units",
  unit: (id: string) => `/units/${id}`,
  unitLocation: (id: string) => `/units/${id}/location`,
  vehicles: "/vehicles",
  resourcesStatus: "/resources/status",
  resourcesHistory: "/resources/history",

  spatialBBox: "/spatial/within-bbox",

  route: "/routing/route",
  eta: "/routing/eta",
} as const;
