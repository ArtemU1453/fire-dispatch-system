/**
 * Bottom panel — Operational Timeline. Auto-updating, searchable and filterable
 * list of incident events, windowed with the shared virtual-list hook.
 */
import { memo, useEffect, useMemo, useRef, useState } from "react";
import { Search } from "lucide-react";
import { Panel } from "@/components/ui/panel";
import { Loader } from "@/components/ui/loader";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useVirtualList } from "@/features/dispatcher-workspace/hooks";
import { useTimeline } from "../hooks";
import { useManagementStore } from "../store/management.store";
import { filterTimeline, timelineCategory } from "../utils";
import type { TimelineCategory } from "../types";

const ROW_HEIGHT = 52;

const CATEGORY_OPTIONS: Array<{ value: TimelineCategory; label: string }> = [
  { value: "all", label: "Все события" },
  { value: "registration", label: "Регистрация" },
  { value: "assignment", label: "Назначения" },
  { value: "status", label: "Смена статуса" },
  { value: "route", label: "Маршруты" },
  { value: "message", label: "Сообщения" },
  { value: "decision", label: "Решения" },
];

const CATEGORY_VARIANT: Record<string, "default" | "info" | "warning" | "success" | "outline"> = {
  registration: "outline",
  assignment: "warning",
  status: "info",
  route: "default",
  message: "success",
  decision: "outline",
};

function OperationalTimelineBase({ incidentId }: { incidentId: string }) {
  const { data, isLoading, isError } = useTimeline(incidentId);
  const search = useManagementStore((s) => s.timeline.search);
  const category = useManagementStore((s) => s.timeline.category);
  const setFilters = useManagementStore((s) => s.setTimelineFilters);

  const entries = useMemo(() => {
    const sorted = [...(data?.entries ?? [])].sort((a, b) =>
      b.occurred_at.localeCompare(a.occurred_at),
    );
    return filterTimeline(sorted, search, category);
  }, [data?.entries, search, category]);

  const scrollRef = useRef<HTMLDivElement>(null);
  const [viewport, setViewport] = useState(200);
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const update = () => {
      if (el.clientHeight > 0) setViewport(el.clientHeight);
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const { totalHeight, offsetY, items, onScroll } = useVirtualList(
    entries,
    ROW_HEIGHT,
    viewport,
  );

  return (
    <Panel
      title={`Оперативный журнал · ${entries.length}`}
      className="h-full"
      bodyClassName="flex min-h-0 flex-col p-0"
      actions={
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="pointer-events-none absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" aria-hidden />
            <Input
              value={search}
              onChange={(e) => setFilters({ search: e.target.value })}
              placeholder="Поиск по журналу…"
              aria-label="Поиск по журналу"
              className="h-8 w-48 pl-7 text-xs"
            />
          </div>
          <Select value={category} onValueChange={(v) => setFilters({ category: v as TimelineCategory })}>
            <SelectTrigger aria-label="Категория события" className="h-8 w-40 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CATEGORY_OPTIONS.map((o) => (
                <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      }
    >
      <div ref={scrollRef} onScroll={onScroll} className="min-h-0 flex-1 overflow-y-auto" aria-busy={isLoading}>
        {isLoading ? (
          <div className="flex h-full items-center justify-center"><Loader label="Загрузка журнала…" /></div>
        ) : isError ? (
          <p className="p-3 text-sm text-danger">Не удалось загрузить журнал.</p>
        ) : entries.length === 0 ? (
          <p className="p-3 text-sm text-muted-foreground">Событий нет.</p>
        ) : (
          <div style={{ height: totalHeight, position: "relative" }}>
            <div style={{ transform: `translateY(${offsetY}px)` }}>
              {items.map(({ item }) => {
                const cat = timelineCategory(item.event_type);
                return (
                  <div
                    key={item.id}
                    style={{ height: ROW_HEIGHT }}
                    className="flex items-center gap-3 border-b border-border px-3 text-xs"
                  >
                    <span className="w-16 shrink-0 tabular-nums text-muted-foreground">
                      {new Date(item.occurred_at).toLocaleTimeString("ru-RU")}
                    </span>
                    <Badge variant={CATEGORY_VARIANT[cat] ?? "default"}>{cat}</Badge>
                    <span className="flex-1 truncate">
                      <span className="font-medium">{item.title}</span>
                      {item.detail ? <span className="text-muted-foreground"> · {item.detail}</span> : null}
                    </span>
                    {item.actor_name && (
                      <span className="shrink-0 text-[11px] text-muted-foreground">{item.actor_name}</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </Panel>
  );
}

export const OperationalTimeline = memo(OperationalTimelineBase);
