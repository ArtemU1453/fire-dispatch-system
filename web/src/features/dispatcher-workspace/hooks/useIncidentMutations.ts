/**
 * Incident mutations with optimistic updates and cache invalidation.
 */
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/components/ui/use-toast";
import { IncidentService } from "../api";
import { dispatcherKeys } from "./queryKeys";
import type { AssignUnitInput, Incident, IncidentStatus } from "../types";

interface StatusVars {
  incidentId: string;
  status: IncidentStatus;
  note?: string;
  actorName?: string;
}

export function useChangeIncidentStatus() {
  const qc = useQueryClient();
  const toast = useToast((s) => s.toast);

  return useMutation({
    mutationFn: (vars: StatusVars) =>
      IncidentService.changeStatus(
        vars.incidentId,
        vars.status,
        vars.note,
        vars.actorName,
      ),
    // Optimistically patch the cached detail so the UI reacts instantly.
    onMutate: async (vars) => {
      const key = dispatcherKeys.incident(vars.incidentId);
      await qc.cancelQueries({ queryKey: key });
      const previous = qc.getQueryData<Incident>(key);
      if (previous) {
        qc.setQueryData<Incident>(key, { ...previous, status: vars.status });
      }
      return { previous, key };
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.previous) qc.setQueryData(ctx.key, ctx.previous);
      toast({
        title: "Не удалось изменить статус",
        description: "Повторите попытку.",
        variant: "danger",
      });
    },
    onSuccess: () => {
      toast({ title: "Статус обновлён" });
    },
    onSettled: (_data, _err, vars) => {
      void qc.invalidateQueries({ queryKey: dispatcherKeys.incident(vars.incidentId) });
      void qc.invalidateQueries({ queryKey: dispatcherKeys.activeIncidents() });
      void qc.invalidateQueries({ queryKey: dispatcherKeys.stats() });
      void qc.invalidateQueries({ queryKey: dispatcherKeys.log() });
    },
  });
}

interface AssignVars {
  incidentId: string;
  units: AssignUnitInput[];
  actorName?: string;
}

export function useAssignUnits() {
  const qc = useQueryClient();
  const toast = useToast((s) => s.toast);

  return useMutation({
    mutationFn: (vars: AssignVars) =>
      IncidentService.assignUnits(vars.incidentId, vars.units, vars.actorName),
    onSuccess: (incident) => {
      qc.setQueryData(dispatcherKeys.incident(incident.id), incident);
      toast({ title: "Подразделения назначены" });
    },
    onError: () =>
      toast({
        title: "Ошибка назначения",
        description: "Не удалось назначить подразделения.",
        variant: "danger",
      }),
    onSettled: (_data, _err, vars) => {
      void qc.invalidateQueries({ queryKey: dispatcherKeys.incident(vars.incidentId) });
      void qc.invalidateQueries({ queryKey: dispatcherKeys.units() });
      void qc.invalidateQueries({ queryKey: dispatcherKeys.stats() });
    },
  });
}
