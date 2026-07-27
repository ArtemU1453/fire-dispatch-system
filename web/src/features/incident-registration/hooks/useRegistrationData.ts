/**
 * Data hooks for the registration workflow (incident types, address search,
 * nearest resources, Dispatch Engine preview).
 */
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import {
  AddressService,
  CatalogService,
  DispatchService,
  NearestService,
} from "../api";
import { registrationKeys } from "./keys";
import { useDebouncedValue } from "./useDebouncedValue";
import { useRegistrationStore } from "../store/registration.store";

/** Incident-type catalog for the form select. */
export function useIncidentTypes() {
  return useQuery({
    queryKey: registrationKeys.incidentTypes(),
    queryFn: ({ signal }) => CatalogService.incidentTypes(signal),
    staleTime: 5 * 60_000,
  });
}

/** Debounced address autocomplete (one request per settled keystroke). */
export function useAddressSearch(term: string, debounceMs = 300) {
  const debounced = useDebouncedValue(term.trim(), debounceMs);
  const enabled = debounced.length >= 3;
  return useQuery({
    queryKey: registrationKeys.addressSearch(debounced),
    queryFn: ({ signal }) => AddressService.search(debounced, 7, signal),
    enabled,
    placeholderData: keepPreviousData,
    staleTime: 60_000,
  });
}

/** Nearby resources around the resolved incident point (Step 3 map). */
export function useNearestResources() {
  const location = useRegistrationStore((s) => s.location);
  return useQuery({
    queryKey: location
      ? registrationKeys.nearest(location.latitude, location.longitude)
      : registrationKeys.nearest(0, 0),
    queryFn: ({ signal }) =>
      NearestService.near(location!.latitude, location!.longitude, 12, signal),
    enabled: Boolean(location),
    staleTime: 30_000,
  });
}

/**
 * Dispatch Engine preview (Step 4). Re-runs whenever the incident point, type
 * or the set of excluded resources changes (dispatcher removed a unit).
 */
export function useDispatchPreview() {
  const location = useRegistrationStore((s) => s.location);
  const form = useRegistrationStore((s) => s.form);
  const excluded = useRegistrationStore((s) => s.excludedResourceIds);

  const enabled = Boolean(location && form.incidentTypeId);

  return useQuery({
    queryKey:
      location && form.incidentTypeId
        ? registrationKeys.preview(
            form.incidentTypeId,
            location.latitude,
            location.longitude,
            excluded,
          )
        : [...registrationKeys.all, "preview", "idle"],
    queryFn: ({ signal }) =>
      DispatchService.preview(
        {
          incidentTypeId: form.incidentTypeId,
          latitude: location!.latitude,
          longitude: location!.longitude,
          address: location!.address,
          excludedResourceIds: excluded,
        },
        signal,
      ),
    enabled,
    staleTime: 15_000,
  });
}
