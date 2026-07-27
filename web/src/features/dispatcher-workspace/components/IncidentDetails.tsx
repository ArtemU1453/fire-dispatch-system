/**
 * IncidentDetails — the right operational panel. Shows the full card for the
 * selected incident (address, description, category, priority, coordinates,
 * status), its assigned units with per-unit ETA, and the incident timeline.
 * Includes a guarded status-change control driven by `allowed_transitions`.
 */
import { memo, useState } from "react";
import {
  MapPin,
  Crosshair,
  Users,
  Clock,
  History as HistoryIcon,
  ArrowRight,
} from "lucide-react";
import { Panel } from "@/components/ui/panel";
import { Loader } from "@/components/ui/loader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  useIncidentDetails,
  useIncidentEtas,
  useChangeIncidentStatus,
} from "../hooks";
import { useDispatcherStore } from "../store/dispatcher.store";
import {
  categoryLabel,
  formatEta,
  priorityLabel,
  priorityVariant,
  statusLabel,
} from "../utils/format";
import type { IncidentStatus } from "../types";

function StatusChanger({
  incidentId,
  current,
  allowed,
}: {
  incidentId: string;
  current: IncidentStatus;
  allowed: IncidentStatus[];
}) {
  const [next, setNext] = useState<IncidentStatus | "">("");
  const mutation = useChangeIncidentStatus();
  const options = allowed.filter((s) => s !== current);

  if (options.length === 0) {
    return (
      <p className="text-xs text-muted-foreground">
        Нет доступных переходов статуса.
      </p>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <Select value={next} onValueChange={(v) => setNext(v as IncidentStatus)}>
        <SelectTrigger aria-label="Новый статус" className="h-8 flex-1 text-xs">
          <SelectValue placeholder="Изменить статус…" />
        </SelectTrigger>
        <SelectContent>
          {options.map((s) => (
            <SelectItem key={s} value={s}>
              {statusLabel(s)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Button
        size="sm"
        disabled={!next || mutation.isPending}
        onClick={() => next && mutation.mutate({ incidentId, status: next })}
      >
        {mutation.isPending ? "…" : "Применить"}
      </Button>
    </div>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-3 py-1 text-xs">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right font-medium">{value}</span>
    </div>
  );
}

function IncidentDetailsBase() {
  const selectedId = useDispatcherStore((s) => s.selectedIncidentId);
  const requestFlyTo = useDispatcherStore((s) => s.requestFlyTo);
  const { data: incident, isLoading, isError } = useIncidentDetails(selectedId);
  const { etas } = useIncidentEtas(incident);

  if (!selectedId) {
    return (
      <Panel title="Карточка происшествия" className="h-full">
        <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-muted-foreground">
          <Crosshair className="h-8 w-8" aria-hidden />
          <p className="text-sm">Выберите происшествие из списка или на карте.</p>
        </div>
      </Panel>
    );
  }

  if (isLoading) {
    return (
      <Panel title="Карточка происшествия" className="h-full">
        <div className="flex h-full items-center justify-center">
          <Loader label="Загрузка карточки…" />
        </div>
      </Panel>
    );
  }

  if (isError || !incident) {
    return (
      <Panel title="Карточка происшествия" className="h-full">
        <p className="p-2 text-sm text-danger">Не удалось загрузить карточку.</p>
      </Panel>
    );
  }

  const hasCoords = incident.latitude != null && incident.longitude != null;

  return (
    <Panel
      title={`№ ${incident.number}`}
      className="h-full"
      bodyClassName="min-h-0 overflow-y-auto p-0"
      actions={
        <Badge variant={priorityVariant(incident.priority)}>
          {priorityLabel(incident.priority)}
        </Badge>
      }
    >
      <div className="flex flex-col gap-4 p-4">
        {/* Summary */}
        <section>
          <div className="mb-2 flex items-center gap-2">
            <Badge variant="outline">{categoryLabel(incident.category)}</Badge>
            <Badge variant="info">{statusLabel(incident.status)}</Badge>
          </div>
          {incident.title && <p className="text-sm font-semibold">{incident.title}</p>}
          {incident.description && (
            <p className="mt-1 text-xs text-muted-foreground">{incident.description}</p>
          )}
        </section>

        {/* Location */}
        <section className="rounded-md border border-border p-2">
          <div className="mb-1 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            <MapPin className="h-3.5 w-3.5" aria-hidden /> Адрес и координаты
          </div>
          <p className="text-xs">{incident.address ?? "Адрес не указан"}</p>
          {hasCoords && (
            <div className="mt-1 flex items-center justify-between">
              <span className="text-[11px] tabular-nums text-muted-foreground">
                {incident.latitude?.toFixed(5)}, {incident.longitude?.toFixed(5)}
              </span>
              <button
                type="button"
                onClick={() => requestFlyTo(incident.id)}
                className="text-[11px] text-info hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                Показать на карте
              </button>
            </div>
          )}
        </section>

        {/* Meta */}
        <section className="rounded-md border border-border p-2">
          <Row label="Категория" value={categoryLabel(incident.category)} />
          <Row label="Источник" value={incident.source} />
          <Row label="Приоритет" value={priorityLabel(incident.priority)} />
          <Row label="Статус" value={statusLabel(incident.status)} />
          {incident.danger_level && <Row label="Уровень опасности" value={incident.danger_level} />}
          <Row
            label="Зарегистрировано"
            value={new Date(incident.reported_at).toLocaleString("ru-RU")}
          />
        </section>

        {/* Status change */}
        <section>
          <div className="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Управление статусом
          </div>
          <StatusChanger
            incidentId={incident.id}
            current={incident.status}
            allowed={incident.allowed_transitions}
          />
        </section>

        {/* Assigned units */}
        <section>
          <div className="mb-1.5 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            <Users className="h-3.5 w-3.5" aria-hidden /> Назначенные подразделения
            <span className="ml-auto tabular-nums">{incident.dispatches.length}</span>
          </div>
          {incident.dispatches.length === 0 ? (
            <p className="text-xs text-muted-foreground">Подразделения не назначены.</p>
          ) : (
            <ul className="flex flex-col gap-1.5">
              {incident.dispatches.map((d) => (
                <li
                  key={d.id}
                  className="flex items-center justify-between rounded-md border border-border px-2 py-1.5 text-xs"
                >
                  <div className="flex flex-col">
                    <span className="font-medium">{d.role}</span>
                    <span className="text-[11px] text-muted-foreground">{d.status}</span>
                  </div>
                  <span className="flex items-center gap-1 tabular-nums text-info">
                    <Clock className="h-3 w-3" aria-hidden />
                    {formatEta(etas[d.resource_id] ?? d.eta_seconds ?? null)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* Timeline */}
        <section>
          <div className="mb-1.5 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            <HistoryIcon className="h-3.5 w-3.5" aria-hidden /> История
          </div>
          {incident.timeline.length === 0 ? (
            <p className="text-xs text-muted-foreground">Событий пока нет.</p>
          ) : (
            <ol className="flex flex-col gap-2">
              {[...incident.timeline]
                .sort((a, b) => b.occurred_at.localeCompare(a.occurred_at))
                .map((e) => (
                  <li key={e.id} className="flex gap-2 text-xs">
                    <ArrowRight className="mt-0.5 h-3 w-3 shrink-0 text-muted-foreground" aria-hidden />
                    <div>
                      <p className="font-medium">{e.title}</p>
                      {e.detail && <p className="text-muted-foreground">{e.detail}</p>}
                      <p className="text-[10px] text-muted-foreground">
                        {new Date(e.occurred_at).toLocaleString("ru-RU")}
                        {e.actor_name ? ` · ${e.actor_name}` : ""}
                      </p>
                    </div>
                  </li>
                ))}
            </ol>
          )}
        </section>
      </div>
    </Panel>
  );
}

export const IncidentDetails = memo(IncidentDetailsBase);
