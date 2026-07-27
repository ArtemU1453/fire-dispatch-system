/**
 * Centralised TanStack Query keys for the dispatcher workspace. A single source
 * of truth makes cache invalidation from the socket layer precise and typo-safe.
 */
export const dispatcherKeys = {
  all: ["dispatcher"] as const,
  stats: () => [...dispatcherKeys.all, "stats"] as const,
  incidents: () => [...dispatcherKeys.all, "incidents"] as const,
  activeIncidents: () => [...dispatcherKeys.incidents(), "active"] as const,
  incident: (id: string) => [...dispatcherKeys.incidents(), "detail", id] as const,
  incidentTimeline: (id: string) =>
    [...dispatcherKeys.incidents(), "timeline", id] as const,
  units: () => [...dispatcherKeys.all, "units"] as const,
  resourceStatus: () => [...dispatcherKeys.all, "resource-status"] as const,
  mapObjects: () => [...dispatcherKeys.all, "map-objects"] as const,
  log: () => [...dispatcherKeys.all, "log"] as const,
} as const;
