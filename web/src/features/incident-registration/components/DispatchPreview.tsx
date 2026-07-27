/**
 * Step 4 — Dispatch Preview. Shows the Dispatch Engine recommendation:
 * confidence, sufficiency, primary/reserve units with distance and rationale.
 * The recommendation is applied to the store (preselects primary units).
 */
import { memo, useEffect } from "react";
import { BrainCircuit, AlertTriangle, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Panel } from "@/components/ui/panel";
import { Loader } from "@/components/ui/loader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useDispatchPreview } from "../hooks";
import { useRegistrationStore } from "../store/registration.store";
import { CONFIDENCE_LABELS, formatDistance } from "../utils/labels";
import type { ConfidenceLevel, RecommendedUnit } from "../types";

const CONFIDENCE_TONE: Record<ConfidenceLevel, string> = {
  low: "text-danger",
  medium: "text-warning",
  high: "text-success",
};

function UnitRow({ unit }: { unit: RecommendedUnit }) {
  return (
    <li className="rounded-md border border-border px-2.5 py-2 text-xs">
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium">
          {unit.code} · {unit.name}
        </span>
        <span className="tabular-nums text-muted-foreground">
          {formatDistance(unit.distance_meters)}
        </span>
      </div>
      {unit.reasons.length > 0 && (
        <p className="mt-0.5 text-[11px] text-muted-foreground">
          {unit.reasons.join(" · ")}
        </p>
      )}
    </li>
  );
}

function DispatchPreviewBase() {
  const { data, isLoading, isError, isFetching, refetch } = useDispatchPreview();
  const applyRecommendation = useRegistrationStore((s) => s.applyRecommendation);
  const location = useRegistrationStore((s) => s.location);
  const typeId = useRegistrationStore((s) => s.form.incidentTypeId);

  // Apply the recommendation whenever a fresh one arrives.
  useEffect(() => {
    if (data) applyRecommendation(data);
  }, [data, applyRecommendation]);

  if (!location || !typeId) {
    return (
      <Panel title="Рекомендации AI" className="h-full">
        <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-muted-foreground">
          <BrainCircuit className="h-8 w-8" aria-hidden />
          <p className="text-sm">
            Укажите тип происшествия и адрес — Dispatch Engine подберёт силы.
          </p>
        </div>
      </Panel>
    );
  }

  return (
    <Panel
      title="Рекомендации AI (Dispatch Engine)"
      className="h-full"
      bodyClassName="min-h-0 overflow-y-auto"
      actions={isFetching ? <Loader /> : undefined}
    >
      {isLoading ? (
        <div className="flex h-full items-center justify-center">
          <Loader label="Подбор сил…" />
        </div>
      ) : isError || !data ? (
        <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
          <AlertTriangle className="h-8 w-8 text-danger" aria-hidden />
          <p className="text-sm text-muted-foreground">
            Dispatch Engine недоступен.
          </p>
          <Button size="sm" variant="outline" onClick={() => refetch()}>
            Повторить
          </Button>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {/* Confidence + sufficiency */}
          <div className="flex items-center justify-between rounded-md border border-border bg-panel px-3 py-2">
            <div className="flex flex-col">
              <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
                Уверенность
              </span>
              <span className={cn("text-sm font-semibold", CONFIDENCE_TONE[data.confidence])}>
                {CONFIDENCE_LABELS[data.confidence]} ·{" "}
                {Math.round(data.confidence_score * 100)}%
              </span>
            </div>
            {data.sufficient ? (
              <Badge variant="success">
                <CheckCircle2 className="mr-1 h-3 w-3" aria-hidden /> Достаточно сил
              </Badge>
            ) : (
              <Badge variant="warning">
                <AlertTriangle className="mr-1 h-3 w-3" aria-hidden /> Сил недостаточно
              </Badge>
            )}
          </div>

          {data.missing_capabilities.length > 0 && (
            <p className="rounded-md border border-warning/40 bg-warning/5 px-2.5 py-1.5 text-xs text-warning">
              Не покрыто: {data.missing_capabilities.join(", ")}
            </p>
          )}

          <section>
            <h3 className="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Первоочередные силы ({data.primary_units.length})
            </h3>
            {data.primary_units.length === 0 ? (
              <p className="text-xs text-muted-foreground">Нет доступных подразделений.</p>
            ) : (
              <ul className="flex flex-col gap-1.5">
                {data.primary_units.map((u) => (
                  <UnitRow key={u.id} unit={u} />
                ))}
              </ul>
            )}
          </section>

          {data.reserve_units.length > 0 && (
            <section>
              <h3 className="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                Резерв ({data.reserve_units.length})
              </h3>
              <ul className="flex flex-col gap-1.5">
                {data.reserve_units.map((u) => (
                  <UnitRow key={u.id} unit={u} />
                ))}
              </ul>
            </section>
          )}

          {data.reasons.length > 0 && (
            <p className="text-[11px] text-muted-foreground">
              Обоснование: {data.reasons.join(" · ")}
            </p>
          )}
        </div>
      )}
    </Panel>
  );
}

export const DispatchPreview = memo(DispatchPreviewBase);
