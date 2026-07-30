/**
 * Operational mutations for the management screen. Every action goes through the
 * real backend, invalidates the affected caches (so the UI updates without a
 * reload) and cross-invalidates the dispatcher workspace. User-facing toasts on
 * success/failure with retry via re-invoking the action.
 */
import { useCallback } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/components/ui/use-toast";
import { useUserStore } from "@/store/user.store";
import { dispatcherKeys } from "@/features/dispatcher-workspace/hooks/queryKeys";
import { ManagementService } from "../api";
import { managementKeys } from "./keys";
import type { IncidentStatus } from "../types";

export function useManagementActions(incidentId: string) {
  const qc = useQueryClient();
  const toast = useToast((s) => s.toast);
  const actorName = useUserStore((s) => s.user?.fullName ?? undefined);

  const invalidate = useCallback(() => {
    void qc.invalidateQueries({ queryKey: managementKeys.incident(incidentId) });
    void qc.invalidateQueries({ queryKey: managementKeys.timeline(incidentId) });
    void qc.invalidateQueries({ queryKey: managementKeys.units() });
    // Cross-refresh the dispatcher workspace.
    void qc.invalidateQueries({ queryKey: dispatcherKeys.activeIncidents() });
    void qc.invalidateQueries({ queryKey: dispatcherKeys.stats() });
    void qc.invalidateQueries({ queryKey: dispatcherKeys.mapObjects() });
    void qc.invalidateQueries({ queryKey: dispatcherKeys.log() });
  }, [qc, incidentId]);

  const fail = useCallback(
    (title: string) => (_e: unknown) =>
      toast({ title, description: "Повторите операцию.", variant: "danger" }),
    [toast],
  );

  const assign = useMutation({
    mutationFn: (resourceIds: string[]) =>
      ManagementService.assignUnits(
        incidentId,
        resourceIds.map((id, i) => ({ resource_id: id, role: i === 0 ? "primary" : "support" })),
        actorName,
      ),
    onSuccess: () => {
      invalidate();
      toast({ title: "Подразделения назначены", variant: "success" });
    },
    onError: fail("Ошибка назначения"),
  });

  const release = useMutation({
    mutationFn: (unitId: string) => ManagementService.releaseUnit(unitId, actorName),
    onSuccess: () => {
      invalidate();
      toast({ title: "Высылка отменена", variant: "success" });
    },
    onError: fail("Не удалось отменить высылку"),
  });

  const replace = useMutation({
    mutationFn: async (vars: { oldUnitId: string; newResourceId: string }) => {
      await ManagementService.releaseUnit(vars.oldUnitId, actorName);
      await ManagementService.assignUnits(
        incidentId,
        [{ resource_id: vars.newResourceId, role: "primary" }],
        actorName,
      );
    },
    onSuccess: () => {
      invalidate();
      toast({ title: "Подразделение заменено", variant: "success" });
    },
    onError: fail("Ошибка замены"),
  });

  const changeUnitStatus = useMutation({
    mutationFn: (vars: { unitId: string; statusCode: string }) =>
      ManagementService.changeUnitStatus(vars.unitId, vars.statusCode, incidentId, actorName),
    onSuccess: () => invalidate(),
    onError: fail("Не удалось изменить статус"),
  });

  const changeLevel = useMutation({
    mutationFn: (priority: string) =>
      ManagementService.updateIncident(incidentId, { priority, actor_name: actorName }),
    onSuccess: () => {
      invalidate();
      toast({ title: "Уровень вызова изменён", variant: "success" });
    },
    onError: fail("Не удалось изменить уровень"),
  });

  const addMessage = useMutation({
    mutationFn: (text: string) =>
      ManagementService.addComment(incidentId, text, actorName),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: managementKeys.timeline(incidentId) });
      void qc.invalidateQueries({ queryKey: managementKeys.incident(incidentId) });
      toast({ title: "Сообщение добавлено", variant: "success" });
    },
    onError: fail("Не удалось добавить сообщение"),
  });

  const close = useMutation({
    mutationFn: (vars: { status: IncidentStatus; note?: string }) =>
      ManagementService.changeIncidentStatus(
        incidentId,
        vars.status,
        vars.note,
        actorName,
      ),
    onSuccess: () => {
      invalidate();
      toast({ title: "Статус происшествия обновлён", variant: "success" });
    },
    onError: fail("Не удалось изменить статус происшествия"),
  });

  return { assign, release, replace, changeUnitStatus, changeLevel, addMessage, close };
}
