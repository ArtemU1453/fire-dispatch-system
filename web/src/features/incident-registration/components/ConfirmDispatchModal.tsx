/**
 * Step 6 — confirmation modal. Lists the units to be sent (with ETA), surfaces
 * warnings (insufficient forces, uncovered capabilities) and special conditions
 * before the dispatcher commits. Ctrl+Enter confirms (handled by the page).
 */
import { memo } from "react";
import { AlertTriangle, Send, Clock } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useRegistrationStore } from "../store/registration.store";
import { useSelectedEtas } from "../hooks";
import { formatDistance, formatEta } from "../utils/labels";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  isSubmitting: boolean;
}

function ConfirmDispatchModalBase({
  open,
  onOpenChange,
  onConfirm,
  isSubmitting,
}: Props) {
  const selected = useRegistrationStore((s) => s.selectedUnits);
  const recommendation = useRegistrationStore((s) => s.recommendation);
  const location = useRegistrationStore((s) => s.location);
  const priority = useRegistrationStore((s) => s.form.priority);
  const etas = useSelectedEtas();

  const warnings: string[] = [];
  if (recommendation && !recommendation.sufficient) {
    warnings.push("Рекомендованных сил недостаточно для типовой обстановки.");
  }
  if (recommendation && recommendation.missing_capabilities.length > 0) {
    warnings.push(
      `Не покрыты возможности: ${recommendation.missing_capabilities.join(", ")}.`,
    );
  }
  if (selected.length === 0) {
    warnings.push("Подразделения не выбраны — будет создана только карточка.");
  }

  const specialConditions: string[] = [];
  if (priority === "critical") specialConditions.push("Критический приоритет");
  if (priority === "high") specialConditions.push("Повышенный приоритет");

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Подтвердить высылку подразделений?</DialogTitle>
        </DialogHeader>

        <div className="flex max-h-[60vh] flex-col gap-3 overflow-y-auto">
          {location && (
            <p className="text-sm">
              <span className="text-muted-foreground">Адрес: </span>
              {location.address}
            </p>
          )}

          {specialConditions.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {specialConditions.map((c) => (
                <Badge key={c} variant="danger">
                  {c}
                </Badge>
              ))}
            </div>
          )}

          {/* Units + ETA */}
          <section>
            <h3 className="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              К высылке ({selected.length})
            </h3>
            {selected.length === 0 ? (
              <p className="text-xs text-muted-foreground">Нет выбранных подразделений.</p>
            ) : (
              <ul className="flex flex-col gap-1">
                {selected.map((u, i) => (
                  <li
                    key={u.resource_id}
                    className="flex items-center justify-between gap-2 rounded-md border border-border px-2.5 py-1.5 text-xs"
                  >
                    <span className="flex items-center gap-2">
                      <span className="w-4 text-center tabular-nums text-muted-foreground">
                        {i + 1}
                      </span>
                      <span className="font-medium">
                        {u.code} · {u.name}
                      </span>
                    </span>
                    <span className="flex items-center gap-3 tabular-nums text-muted-foreground">
                      <span>{formatDistance(u.distance_meters)}</span>
                      <span className="flex items-center gap-1 text-info">
                        <Clock className="h-3 w-3" aria-hidden />
                        {formatEta(etas[u.resource_id])}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* Warnings */}
          {warnings.length > 0 && (
            <div className="flex flex-col gap-1 rounded-md border border-warning/40 bg-warning/5 px-3 py-2">
              {warnings.map((w) => (
                <p key={w} className="flex items-start gap-1.5 text-xs text-warning">
                  <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
                  {w}
                </p>
              ))}
            </div>
          )}
        </div>

        <div className="mt-2 flex justify-end gap-2">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isSubmitting}
          >
            Отмена
          </Button>
          <Button onClick={onConfirm} disabled={isSubmitting}>
            <Send className="mr-1.5 h-4 w-4" aria-hidden />
            {isSubmitting ? "Передача…" : "Передать в Dispatch Engine"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export const ConfirmDispatchModal = memo(ConfirmDispatchModalBase);
