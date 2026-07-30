/**
 * ResourceManager — the modals that mutate the incident's composition:
 *  - AddResourceModal   (add units / reserves, with send order)
 *  - ReplaceResourceModal (swap one unit for another)
 *  - UnitCardModal      (view a unit's card)
 * All operations go through the real backend via `useManagementActions`.
 */
import { memo, useMemo, useState } from "react";
import { ArrowUp, ArrowDown, Plus, X } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Loader } from "@/components/ui/loader";
import { cn } from "@/lib/utils";
import { useAvailableUnits, useManagementActions } from "../hooks";
import type { AssignedResource } from "../types";
import type { Unit } from "@/features/dispatcher-workspace/types/resource";

// --- Add ---------------------------------------------------------------------
export const AddResourceModal = memo(function AddResourceModal({
  incidentId,
  open,
  onOpenChange,
  assignedIds,
  reserve = false,
}: {
  incidentId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  assignedIds: string[];
  reserve?: boolean;
}) {
  const { available, isLoading } = useAvailableUnits(assignedIds);
  const { assign } = useManagementActions(incidentId);
  const [selected, setSelected] = useState<Unit[]>([]);
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return available.filter(
      (u) =>
        !selected.some((s) => s.id === u.id) &&
        (!q || `${u.code} ${u.name}`.toLowerCase().includes(q)),
    );
  }, [available, selected, search]);

  const move = (id: string, dir: -1 | 1) =>
    setSelected((list) => {
      const i = list.findIndex((u) => u.id === id);
      const j = i + dir;
      if (i < 0 || j < 0 || j >= list.length) return list;
      const next = [...list];
      [next[i], next[j]] = [next[j], next[i]];
      return next;
    });

  const submit = () => {
    if (selected.length === 0) return;
    assign.mutate(
      selected.map((u) => u.id),
      { onSuccess: () => { setSelected([]); onOpenChange(false); } },
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{reserve ? "Добавить резерв" : "Добавить подразделение"}</DialogTitle>
        </DialogHeader>

        {selected.length > 0 && (
          <div>
            <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Порядок выезда
            </p>
            <ol className="mb-2 flex flex-col gap-1">
              {selected.map((u, i) => (
                <li key={u.id} className="flex items-center gap-2 rounded-md border border-border px-2 py-1 text-xs">
                  <span className="w-4 text-center tabular-nums text-muted-foreground">{i + 1}</span>
                  <span className="flex-1 truncate">{u.code} · {u.name}</span>
                  <Button size="icon" variant="ghost" className="h-6 w-6" aria-label="Выше" disabled={i === 0} onClick={() => move(u.id, -1)}>
                    <ArrowUp className="h-3.5 w-3.5" aria-hidden />
                  </Button>
                  <Button size="icon" variant="ghost" className="h-6 w-6" aria-label="Ниже" disabled={i === selected.length - 1} onClick={() => move(u.id, 1)}>
                    <ArrowDown className="h-3.5 w-3.5" aria-hidden />
                  </Button>
                  <Button size="icon" variant="ghost" className="h-6 w-6 text-danger" aria-label="Убрать" onClick={() => setSelected((l) => l.filter((x) => x.id !== u.id))}>
                    <X className="h-3.5 w-3.5" aria-hidden />
                  </Button>
                </li>
              ))}
            </ol>
          </div>
        )}

        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Поиск подразделения…"
          aria-label="Поиск подразделения"
          className="h-9"
        />
        <div className="max-h-64 overflow-y-auto rounded-md border border-border">
          {isLoading ? (
            <div className="p-4"><Loader label="Загрузка подразделений…" /></div>
          ) : filtered.length === 0 ? (
            <p className="p-3 text-xs text-muted-foreground">Нет доступных подразделений.</p>
          ) : (
            <ul>
              {filtered.map((u) => (
                <li key={u.id}>
                  <button
                    type="button"
                    onClick={() => setSelected((l) => [...l, u])}
                    className="flex w-full items-center justify-between gap-2 border-b border-border px-3 py-2 text-left text-xs hover:bg-muted/60"
                  >
                    <span className="truncate">{u.code} · {u.name}</span>
                    <span className="flex items-center gap-2">
                      {u.status && <Badge variant="outline">{u.status.name}</Badge>}
                      <Plus className="h-3.5 w-3.5 text-info" aria-hidden />
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="mt-2 flex justify-end gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>Отмена</Button>
          <Button onClick={submit} disabled={selected.length === 0 || assign.isPending}>
            {assign.isPending ? "Назначение…" : `Назначить (${selected.length})`}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
});

// --- Replace -----------------------------------------------------------------
export const ReplaceResourceModal = memo(function ReplaceResourceModal({
  incidentId,
  open,
  onOpenChange,
  target,
  assignedIds,
}: {
  incidentId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  target: AssignedResource | null;
  assignedIds: string[];
}) {
  const { available, isLoading } = useAvailableUnits(assignedIds);
  const { replace } = useManagementActions(incidentId);
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return available.filter((u) => !q || `${u.code} ${u.name}`.toLowerCase().includes(q));
  }, [available, search]);

  const canReplace = Boolean(target?.unitId);

  const pick = (newResourceId: string) => {
    if (!target?.unitId) return;
    replace.mutate(
      { oldUnitId: target.unitId, newResourceId },
      { onSuccess: () => onOpenChange(false) },
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>
            Заменить подразделение{target ? ` ${target.code}` : ""}
          </DialogTitle>
        </DialogHeader>
        {!canReplace ? (
          <p className="text-sm text-muted-foreground">
            Для этого подразделения замена недоступна (нет связанной карточки).
          </p>
        ) : (
          <>
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Поиск замены…"
              aria-label="Поиск замены"
              className="h-9"
            />
            <div className="max-h-64 overflow-y-auto rounded-md border border-border">
              {isLoading ? (
                <div className="p-4"><Loader /></div>
              ) : filtered.length === 0 ? (
                <p className="p-3 text-xs text-muted-foreground">Нет доступных подразделений.</p>
              ) : (
                <ul>
                  {filtered.map((u) => (
                    <li key={u.id}>
                      <button
                        type="button"
                        disabled={replace.isPending}
                        onClick={() => pick(u.id)}
                        className={cn(
                          "flex w-full items-center justify-between gap-2 border-b border-border px-3 py-2 text-left text-xs hover:bg-muted/60",
                          replace.isPending && "opacity-50",
                        )}
                      >
                        <span className="truncate">{u.code} · {u.name}</span>
                        {u.status && <Badge variant="outline">{u.status.name}</Badge>}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </>
        )}
        <div className="mt-2 flex justify-end">
          <Button variant="outline" onClick={() => onOpenChange(false)}>Закрыть</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
});

// --- View unit card ----------------------------------------------------------
export const UnitCardModal = memo(function UnitCardModal({
  open,
  onOpenChange,
  resource,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  resource: AssignedResource | null;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Карточка подразделения</DialogTitle>
        </DialogHeader>
        {resource ? (
          <dl className="flex flex-col gap-1 text-xs">
            <Row k="Код" v={resource.code} />
            <Row k="Наименование" v={resource.name} />
            <Row k="Позывной" v={resource.callSign ?? "—"} />
            <Row k="Роль" v={resource.role} />
            <Row k="Статус (высылка)" v={resource.dispatchStatus} />
            <Row k="Статус (готовность)" v={resource.unitStatus?.name ?? "—"} />
            <Row k="Техника" v={resource.vehicleType ?? "—"} />
            <Row k="Экипаж" v={String(resource.crewCount)} />
          </dl>
        ) : (
          <p className="text-sm text-muted-foreground">Нет данных.</p>
        )}
      </DialogContent>
    </Dialog>
  );
});

function Row({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-3">
      <dt className="text-muted-foreground">{k}</dt>
      <dd className="text-right font-medium">{v}</dd>
    </div>
  );
}
