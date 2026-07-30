/**
 * Left panel — the incident card. Auto-updates (polling + realtime invalidation).
 */
import { memo } from "react";
import { Panel } from "@/components/ui/panel";
import { Loader } from "@/components/ui/loader";
import { Badge } from "@/components/ui/badge";
import {
  categoryLabel,
  priorityLabel,
  priorityVariant,
  statusLabel,
} from "../utils";
import { useIncident } from "../hooks";

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-3 py-1 text-xs">
      <span className="shrink-0 text-muted-foreground">{label}</span>
      <span className="text-right font-medium">{value ?? "—"}</span>
    </div>
  );
}

function IncidentCardBase({ incidentId }: { incidentId: string }) {
  const { data: incident, isLoading, isError } = useIncident(incidentId);

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

  const reported = new Date(incident.reported_at);
  const primaryLocation = incident.locations.find((l) => l.is_primary) ?? incident.locations[0];

  return (
    <Panel
      title={`№ ${incident.number}`}
      className="h-full"
      bodyClassName="min-h-0 overflow-y-auto"
      actions={
        <Badge variant={priorityVariant(incident.priority)}>
          {priorityLabel(incident.priority)}
        </Badge>
      }
    >
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center gap-1.5">
          <Badge variant="outline">{categoryLabel(incident.category)}</Badge>
          <Badge variant="info">{statusLabel(incident.status)}</Badge>
        </div>

        {incident.title && <p className="text-sm font-semibold">{incident.title}</p>}
        {incident.description && (
          <p className="text-xs text-muted-foreground">{incident.description}</p>
        )}

        <section className="rounded-md border border-border p-2">
          <Field label="Тип / категория" value={categoryLabel(incident.category)} />
          <Field label="Адрес" value={incident.address ?? primaryLocation?.address} />
          <Field
            label="Координаты"
            value={
              incident.latitude != null && incident.longitude != null
                ? `${incident.latitude.toFixed(5)}, ${incident.longitude.toFixed(5)}`
                : "—"
            }
          />
          <Field label="Дата" value={reported.toLocaleDateString("ru-RU")} />
          <Field
            label="Время"
            value={reported.toLocaleTimeString("ru-RU", { hour12: false })}
          />
          <Field label="Приоритет / уровень" value={priorityLabel(incident.priority)} />
          <Field label="Статус" value={statusLabel(incident.status)} />
          {incident.danger_level && (
            <Field label="Уровень опасности" value={incident.danger_level} />
          )}
        </section>

        <section className="rounded-md border border-border p-2">
          <Field label="Заявитель" value={incident.reporter_name} />
          <Field label="Телефон" value={incident.reporter_contact} />
          <Field label="Источник" value={incident.source} />
        </section>
      </div>
    </Panel>
  );
}

export const IncidentCard = memo(IncidentCardBase);
