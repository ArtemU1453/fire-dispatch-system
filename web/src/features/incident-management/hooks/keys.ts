/** TanStack Query keys for operational incident management. */
export const managementKeys = {
  all: ["management"] as const,
  incident: (id: string) => [...managementKeys.all, "incident", id] as const,
  timeline: (id: string) => [...managementKeys.all, "timeline", id] as const,
  units: () => [...managementKeys.all, "units"] as const,
  statusCatalog: () => [...managementKeys.all, "status-catalog"] as const,
} as const;
