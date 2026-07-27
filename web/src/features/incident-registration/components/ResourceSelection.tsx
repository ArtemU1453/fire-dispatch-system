/**
 * Step 5 — modify the composition. The dispatcher can remove a unit, reorder
 * the send order, add a reserve or a nearby unit, and see why each was
 * recommended. Removing a unit re-runs the Dispatch Engine preview (the store
 * records it as excluded), so replacements are proposed automatically.
 */
import { memo } from "react";
import { ArrowUp, ArrowDown, X, Plus, Info } from "lucide-react";
import { Panel } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useNearestResources } from "../hooks";
import { useRegistrationStore } from "../store/registration.store";
import { formatDistance } from "../utils/labels";
import { nearestToSelected, recommendedToSelected } from "../utils/select";

function ResourceSelectionBase() {
  const selected = useRegistrationStore((s) => s.selectedUnits);
  const recommendation = useRegistrationStore((s) => s.recommendation);
  const removeUnit = useRegistrationStore((s) => s.removeUnit);
  const moveUnit = useRegistrationStore((s) => s.moveUnit);
  const addUnit = useRegistrationStore((s) => s.addUnit);
  const { data: nearest = [] } = useNearestResources();

  const selectedIds = new Set(selected.map((u) => u.resource_id));
  const reserves = (recommendation?.reserve_units ?? []).filter(
    (u) => !selectedIds.has(u.resource_id),
  );
  const addableNearest = nearest.filter((u) => !selectedIds.has(u.id));

  return (
    <Panel
      title={`Состав сил · ${selected.length}`}
      className="h-full"
      bodyClassName="min-h-0 overflow-y-auto"
    >
      <div className="flex flex-col gap-4">
        {/* Chosen units, in send order */}
        <section>
          <h3 className="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            К высылке (по порядку)
          </h3>
          {selected.length === 0 ? (
            <p className="text-xs text-muted-foreground">
              Подразделения не выбраны. Добавьте из рекомендаций ниже.
            </p>
          ) : (
            <ol className="flex flex-col gap-1.5">
              {selected.map((u, i) => (
                <li
                  key={u.resource_id}
                  className="flex items-center gap-2 rounded-md border border-border px-2.5 py-2 text-xs"
                >
                  <span className="w-5 text-center font-semibold tabular-nums text-muted-foreground">
                    {i + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5">
                      <span className="truncate font-medium">
                        {u.code} · {u.name}
                      </span>
                      {i === 0 && <Badge variant="info">Головное</Badge>}
                    </div>
                    <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
                      <span>{formatDistance(u.distance_meters)}</span>
                      {u.reasons.length > 0 && (
                        <span className="flex items-center gap-0.5 truncate">
                          <Info className="h-3 w-3 shrink-0" aria-hidden />
                          {u.reasons[0]}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-0.5">
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-6 w-6"
                      aria-label="Выше в очереди"
                      disabled={i === 0}
                      onClick={() => moveUnit(u.resource_id, -1)}
                    >
                      <ArrowUp className="h-3.5 w-3.5" aria-hidden />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-6 w-6"
                      aria-label="Ниже в очереди"
                      disabled={i === selected.length - 1}
                      onClick={() => moveUnit(u.resource_id, 1)}
                    >
                      <ArrowDown className="h-3.5 w-3.5" aria-hidden />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-6 w-6 text-danger"
                      aria-label="Исключить подразделение"
                      onClick={() => removeUnit(u.resource_id)}
                    >
                      <X className="h-3.5 w-3.5" aria-hidden />
                    </Button>
                  </div>
                </li>
              ))}
            </ol>
          )}
        </section>

        {/* Reserve from the recommendation */}
        {reserves.length > 0 && (
          <section>
            <h3 className="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Резерв (рекомендация)
            </h3>
            <ul className="flex flex-col gap-1.5">
              {reserves.map((u) => (
                <li
                  key={u.id}
                  className="flex items-center justify-between gap-2 rounded-md border border-dashed border-border px-2.5 py-2 text-xs"
                >
                  <div className="min-w-0">
                    <span className="truncate font-medium">
                      {u.code} · {u.name}
                    </span>
                    <span className="ml-2 text-[11px] text-muted-foreground">
                      {formatDistance(u.distance_meters)}
                    </span>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => addUnit(recommendedToSelected(u))}
                  >
                    <Plus className="mr-1 h-3 w-3" aria-hidden /> Добавить
                  </Button>
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Add any nearby unit */}
        {addableNearest.length > 0 && (
          <section>
            <h3 className="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Ближайшие подразделения
            </h3>
            <ul className="flex flex-col gap-1.5">
              {addableNearest.slice(0, 8).map((u) => (
                <li
                  key={u.id}
                  className="flex items-center justify-between gap-2 rounded-md border border-border px-2.5 py-2 text-xs"
                >
                  <div className="min-w-0">
                    <span className="truncate font-medium">
                      {u.code} · {u.name}
                    </span>
                    <span className="ml-2 text-[11px] text-muted-foreground">
                      {formatDistance(u.distance_meters)}
                      {u.availability_status ? ` · ${u.availability_status}` : ""}
                    </span>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => addUnit(nearestToSelected(u))}
                  >
                    <Plus className="mr-1 h-3 w-3" aria-hidden /> Добавить
                  </Button>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </Panel>
  );
}

export const ResourceSelection = memo(ResourceSelectionBase);
