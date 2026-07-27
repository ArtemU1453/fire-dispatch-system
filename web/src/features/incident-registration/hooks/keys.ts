/** TanStack Query keys for the registration workflow. */
export const registrationKeys = {
  all: ["registration"] as const,
  incidentTypes: () => [...registrationKeys.all, "incident-types"] as const,
  addressSearch: (q: string) => [...registrationKeys.all, "address", q] as const,
  nearest: (lat: number, lon: number) =>
    [...registrationKeys.all, "nearest", lat, lon] as const,
  preview: (typeId: string, lat: number, lon: number, excluded: string[]) =>
    [...registrationKeys.all, "preview", typeId, lat, lon, [...excluded].sort()] as const,
} as const;
