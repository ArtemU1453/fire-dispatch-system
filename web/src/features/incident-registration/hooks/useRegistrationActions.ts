/**
 * Action hooks: resolving a chosen address into a full location (reverse
 * geocode) and confirming the registration (create incident + assign units →
 * Dispatch Engine), which then auto-refreshes the dispatcher workspace.
 */
import { useCallback, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/components/ui/use-toast";
import { useUserStore } from "@/store/user.store";
import { dispatcherKeys } from "@/features/dispatcher-workspace/hooks/queryKeys";
import { AddressService, RegistrationService } from "../api";
import { useRegistrationStore } from "../store/registration.store";
import type { AddressCandidate } from "../types";

/** Resolve a selected address candidate into a full location (with district). */
export function useResolveAddress() {
  const setLocation = useRegistrationStore((s) => s.setLocation);
  const setStatus = useRegistrationStore((s) => s.setStatus);
  const [isResolving, setIsResolving] = useState(false);

  const resolve = useCallback(
    async (candidate: AddressCandidate) => {
      setIsResolving(true);
      setStatus("locating");
      try {
        // Reverse geocode is best-effort — the point is already known.
        const area = await AddressService.resolveArea(
          candidate.latitude,
          candidate.longitude,
        ).catch(() => null);
        setLocation({
          address: candidate.formatted_address,
          latitude: candidate.latitude,
          longitude: candidate.longitude,
          area,
        });
        setStatus("located");
      } finally {
        setIsResolving(false);
      }
    },
    [setLocation, setStatus],
  );

  return { resolve, isResolving };
}

/** Confirm the dispatch: create the incident, then assign the chosen units. */
export function useConfirmRegistration(onDone?: (incidentNumber: string) => void) {
  const qc = useQueryClient();
  const toast = useToast((s) => s.toast);
  const actorName = useUserStore((s) => s.user?.fullName ?? null);

  const form = useRegistrationStore((s) => s.form);
  const location = useRegistrationStore((s) => s.location);
  const selectedUnits = useRegistrationStore((s) => s.selectedUnits);
  const setStatus = useRegistrationStore((s) => s.setStatus);
  const setCreated = useRegistrationStore((s) => s.setCreated);

  return useMutation({
    mutationFn: async () => {
      if (!location) throw new Error("Адрес не определён");
      const incident = await RegistrationService.createIncident({
        incidentTypeId: form.incidentTypeId,
        category: form.category,
        source: form.source,
        priority: form.priority,
        description: form.description || null,
        address: location.address,
        latitude: location.latitude,
        longitude: location.longitude,
        reporterName: form.reporterName || null,
        reporterContact: form.reporterContact || null,
        actorName,
      });
      if (selectedUnits.length > 0) {
        await RegistrationService.assignUnits(
          incident.id,
          selectedUnits.map((u, i) => ({
            resource_id: u.resource_id,
            role: i === 0 ? "primary" : "support",
          })),
          actorName ?? undefined,
        );
      }
      return incident;
    },
    onMutate: () => setStatus("submitting"),
    onSuccess: (incident) => {
      setCreated(incident.id, incident.number);
      setStatus("submitted");
      // Auto-refresh the dispatcher workspace (Dashboard / list / map / log).
      void qc.invalidateQueries({ queryKey: dispatcherKeys.activeIncidents() });
      void qc.invalidateQueries({ queryKey: dispatcherKeys.stats() });
      void qc.invalidateQueries({ queryKey: dispatcherKeys.units() });
      void qc.invalidateQueries({ queryKey: dispatcherKeys.resourceStatus() });
      void qc.invalidateQueries({ queryKey: dispatcherKeys.mapObjects() });
      void qc.invalidateQueries({ queryKey: dispatcherKeys.log() });
      toast({
        title: "Происшествие зарегистрировано",
        description: `№ ${incident.number} передано в Dispatch Engine`,
        variant: "success",
      });
      onDone?.(incident.number);
    },
    onError: (err: unknown) => {
      const message =
        err && typeof err === "object" && "message" in err
          ? String((err as { message: unknown }).message)
          : "Не удалось передать в Dispatch Engine";
      setStatus("error", message);
      toast({ title: "Ошибка регистрации", description: message, variant: "danger" });
    },
  });
}
