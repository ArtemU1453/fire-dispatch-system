/**
 * IncidentFilters — search, priority filter chips and sort control for the
 * incident list. All state lives in the DispatcherStore.
 */
import { memo, useCallback } from "react";
import { Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { useDispatcherStore } from "../store/dispatcher.store";
import type { IncidentSortKey } from "../store/dispatcher.store";
import { PRIORITY_LABELS } from "../utils/format";
import type { IncidentPriority } from "../types";

const PRIORITIES: IncidentPriority[] = ["critical", "high", "normal", "low"];

const SORTS: Array<{ value: IncidentSortKey; label: string }> = [
  { value: "reported_desc", label: "Сначала новые" },
  { value: "reported_asc", label: "Сначала старые" },
  { value: "priority", label: "По приоритету" },
];

function IncidentFiltersBase() {
  const search = useDispatcherStore((s) => s.filters.search);
  const priorities = useDispatcherStore((s) => s.filters.priorities);
  const sort = useDispatcherStore((s) => s.filters.sort);
  const setFilters = useDispatcherStore((s) => s.setFilters);

  const togglePriority = useCallback(
    (p: IncidentPriority) => {
      const next = priorities.includes(p)
        ? priorities.filter((x) => x !== p)
        : [...priorities, p];
      setFilters({ priorities: next });
    },
    [priorities, setFilters],
  );

  return (
    <div className="flex flex-col gap-2 border-b border-border p-3">
      <div className="relative">
        <Search
          className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden
        />
        <Input
          value={search}
          onChange={(e) => setFilters({ search: e.target.value })}
          placeholder="Поиск: номер, адрес…"
          aria-label="Поиск происшествий"
          className="pl-8 pr-8"
        />
        {search && (
          <button
            type="button"
            onClick={() => setFilters({ search: "" })}
            aria-label="Очистить поиск"
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-0.5 text-muted-foreground hover:text-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <X className="h-3.5 w-3.5" aria-hidden />
          </button>
        )}
      </div>

      <div className="flex items-center gap-1.5" role="group" aria-label="Фильтр по приоритету">
        {PRIORITIES.map((p) => {
          const active = priorities.includes(p);
          return (
            <button
              key={p}
              type="button"
              aria-pressed={active}
              onClick={() => togglePriority(p)}
              className={cn(
                "rounded-full border px-2 py-0.5 text-[11px] font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                active
                  ? "border-transparent bg-primary text-primary-foreground"
                  : "border-border text-muted-foreground hover:text-foreground",
              )}
            >
              {PRIORITY_LABELS[p]}
            </button>
          );
        })}
      </div>

      <Select value={sort} onValueChange={(v) => setFilters({ sort: v as IncidentSortKey })}>
        <SelectTrigger aria-label="Сортировка" className="h-8 text-xs">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {SORTS.map((s) => (
            <SelectItem key={s.value} value={s.value}>
              {s.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

export const IncidentFilters = memo(IncidentFiltersBase);
