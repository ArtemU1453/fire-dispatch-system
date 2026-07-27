/**
 * OperationalLog — the bottom panel: a live, filterable table of recent
 * operational events. Auto-updates via query polling and socket appends.
 */
import { memo, useMemo, useState } from "react";
import { Search } from "lucide-react";
import { Panel } from "@/components/ui/panel";
import { Loader } from "@/components/ui/loader";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useOperationalLog } from "../hooks";
import { useDispatcherStore } from "../store/dispatcher.store";
import type { BadgeVariant } from "../utils/format";
import type { LogCategory, LogEvent, LogLevel } from "../types";

const LEVEL_VARIANT: Record<LogLevel, BadgeVariant> = {
  info: "info",
  success: "success",
  warning: "warning",
  critical: "danger",
};

const CATEGORY_LABELS: Record<LogCategory, string> = {
  incident: "Происшествие",
  resource: "Ресурс",
  dispatch: "Высылка",
  route: "Маршрут",
  system: "Система",
};

const CATEGORY_OPTIONS: Array<{ value: LogCategory | "all"; label: string }> = [
  { value: "all", label: "Все категории" },
  { value: "incident", label: "Происшествия" },
  { value: "dispatch", label: "Высылка" },
  { value: "resource", label: "Ресурсы" },
  { value: "route", label: "Маршруты" },
  { value: "system", label: "Система" },
];

function filterLog(
  events: LogEvent[],
  search: string,
  category: LogCategory | "all",
): LogEvent[] {
  const q = search.trim().toLowerCase();
  return events.filter((e) => {
    if (category !== "all" && e.category !== category) return false;
    if (q && !`${e.action} ${e.message}`.toLowerCase().includes(q)) return false;
    return true;
  });
}

function OperationalLogBase() {
  const { data, isLoading, isError } = useOperationalLog();
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<LogCategory | "all">("all");
  const selectIncident = useDispatcherStore((s) => s.selectIncident);

  const rows = useMemo(
    () => filterLog(data ?? [], search, category),
    [data, search, category],
  );

  return (
    <Panel
      title={`Журнал событий · ${rows.length}`}
      className="h-full"
      bodyClassName="flex min-h-0 flex-col p-0"
      actions={
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search
              className="pointer-events-none absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground"
              aria-hidden
            />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Поиск по журналу…"
              aria-label="Поиск по журналу"
              className="h-8 w-48 pl-7 text-xs"
            />
          </div>
          <Select
            value={category}
            onValueChange={(v) => setCategory(v as LogCategory | "all")}
          >
            <SelectTrigger aria-label="Категория события" className="h-8 w-40 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CATEGORY_OPTIONS.map((o) => (
                <SelectItem key={o.value} value={o.value}>
                  {o.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      }
    >
      <div className="min-h-0 flex-1 overflow-auto" aria-busy={isLoading}>
        {isLoading ? (
          <div className="flex h-full items-center justify-center">
            <Loader label="Загрузка журнала…" />
          </div>
        ) : isError ? (
          <p className="p-3 text-sm text-danger">Не удалось загрузить журнал.</p>
        ) : rows.length === 0 ? (
          <p className="p-3 text-sm text-muted-foreground">Событий нет.</p>
        ) : (
          <Table>
            <TableHeader className="sticky top-0 z-10 bg-panel">
              <TableRow>
                <TableHead className="w-32">Время</TableHead>
                <TableHead className="w-28">Уровень</TableHead>
                <TableHead className="w-32">Категория</TableHead>
                <TableHead>Событие</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((e) => (
                <TableRow
                  key={e.id}
                  className={e.incident_id ? "cursor-pointer" : undefined}
                  onClick={() => e.incident_id && selectIncident(e.incident_id)}
                >
                  <TableCell className="tabular-nums text-xs text-muted-foreground">
                    {new Date(e.occurred_at).toLocaleTimeString("ru-RU")}
                  </TableCell>
                  <TableCell>
                    <Badge variant={LEVEL_VARIANT[e.level]}>{e.level}</Badge>
                  </TableCell>
                  <TableCell className="text-xs">{CATEGORY_LABELS[e.category]}</TableCell>
                  <TableCell className="text-xs">{e.message}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </Panel>
  );
}

export const OperationalLog = memo(OperationalLogBase);
