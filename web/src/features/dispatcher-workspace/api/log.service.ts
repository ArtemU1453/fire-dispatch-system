/**
 * LogService — the operational event log.
 *
 * Seeds from the append-only resource-management history (`/resources/history`,
 * a real endpoint), mapped into the workspace's `LogEvent` shape. Live events
 * arriving over the WebSocket are merged on top by `useOperationalLog`.
 */
import { request } from "@/api/client";
import { endpoints } from "./endpoints";
import type { LogCategory, LogEvent, LogLevel } from "../types";

interface ResourceHistoryEntry {
  id: string;
  resource_id: string | null;
  unit_id: string | null;
  event_type: string;
  from_value: string | null;
  to_value: string | null;
  source: string;
  incident_id: string | null;
  changed_by_name: string | null;
  occurred_at: string;
}

const EVENT_LABELS: Record<string, string> = {
  unit_status_changed: "Статус подразделения изменён",
  vehicle_status_changed: "Статус транспорта изменён",
  personnel_status_changed: "Статус личного состава изменён",
  crew_changed: "Состав расчёта изменён",
  crew_member_changed: "Изменение члена расчёта",
  assigned: "Назначение на происшествие",
  returned: "Возврат подразделения",
};

function levelFor(eventType: string): LogLevel {
  if (eventType === "assigned") return "warning";
  if (eventType === "returned") return "success";
  return "info";
}

function categoryFor(eventType: string): LogCategory {
  if (eventType === "assigned" || eventType === "returned") return "dispatch";
  return "resource";
}

function toLogEvent(entry: ResourceHistoryEntry): LogEvent {
  const label = EVENT_LABELS[entry.event_type] ?? entry.event_type;
  const transition =
    entry.from_value || entry.to_value
      ? ` (${entry.from_value ?? "—"} → ${entry.to_value ?? "—"})`
      : "";
  return {
    id: entry.id,
    occurred_at: entry.occurred_at,
    level: levelFor(entry.event_type),
    category: categoryFor(entry.event_type),
    action: label,
    message: `${label}${transition}${
      entry.changed_by_name ? ` · ${entry.changed_by_name}` : ""
    }`,
    incident_id: entry.incident_id,
    unit_id: entry.unit_id,
  };
}

export const LogService = {
  async recent(limit = 100, signal?: AbortSignal): Promise<LogEvent[]> {
    const rows = await request<ResourceHistoryEntry[]>({
      url: endpoints.resourcesHistory,
      method: "GET",
      params: { limit },
      signal,
    });
    return rows.map(toLogEvent);
  },
};

export type LogServiceType = typeof LogService;
