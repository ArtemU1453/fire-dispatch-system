/**
 * Presentation helpers: Russian labels and semantic colour tokens for incident
 * enums. Colours map to the shared Enterprise palette (see styles/index.css).
 */
import type {
  IncidentCategory,
  IncidentPriority,
  IncidentStatus,
} from "../types";

export const STATUS_LABELS: Record<IncidentStatus, string> = {
  created: "Создано",
  checking: "Проверка",
  confirmed: "Подтверждено",
  selecting: "Подбор сил",
  dispatch_confirmed: "Подтверждение",
  dispatched: "Высылка",
  on_scene: "На месте",
  localized: "Локализация",
  liquidated: "Ликвидация",
  completed: "Завершено",
  archived: "Архив",
  cancelled: "Отменено",
};

export const PRIORITY_LABELS: Record<IncidentPriority, string> = {
  low: "Низкий",
  normal: "Обычный",
  high: "Высокий",
  critical: "Критический",
};

export const CATEGORY_LABELS: Record<IncidentCategory, string> = {
  fire: "Пожар",
  road_accident: "ДТП",
  rescue: "Спасение",
  chemical: "Химическая ЧС",
  wildfire: "Природный пожар",
  false_alarm: "Ложный вызов",
  special_ops: "Спецоперация",
  service_ops: "Служебные работы",
  other: "Прочее",
};

/** Badge variant for a priority (maps to the shared Badge component variants). */
export type BadgeVariant =
  | "default"
  | "danger"
  | "warning"
  | "success"
  | "info"
  | "outline";

export function priorityVariant(priority: IncidentPriority): BadgeVariant {
  switch (priority) {
    case "critical":
      return "danger";
    case "high":
      return "warning";
    case "normal":
      return "info";
    case "low":
    default:
      return "outline";
  }
}

/** Left-edge colour bar per priority (HSL var references). */
export function priorityColor(priority: IncidentPriority): string {
  switch (priority) {
    case "critical":
      return "hsl(var(--danger))";
    case "high":
      return "hsl(var(--warning))";
    case "normal":
      return "hsl(var(--info))";
    case "low":
    default:
      return "hsl(var(--muted-foreground))";
  }
}

/** Whether a status is terminal (closed/archived/cancelled). */
export function isClosedStatus(status: IncidentStatus): boolean {
  return status === "completed" || status === "archived" || status === "cancelled";
}

export function statusLabel(status: IncidentStatus): string {
  return STATUS_LABELS[status] ?? status;
}

export function priorityLabel(priority: IncidentPriority): string {
  return PRIORITY_LABELS[priority] ?? priority;
}

export function categoryLabel(category: IncidentCategory): string {
  return CATEGORY_LABELS[category] ?? category;
}

/** Format a duration in seconds as a compact ru string ("7 мин", "1 ч 5 мин"). */
export function formatEta(seconds: number | null | undefined): string {
  if (seconds == null || Number.isNaN(seconds)) return "—";
  const total = Math.round(seconds / 60);
  if (total < 60) return `${total} мин`;
  const h = Math.floor(total / 60);
  const m = total % 60;
  return m ? `${h} ч ${m} мин` : `${h} ч`;
}

/** Relative "X мин назад" using an absolute ISO timestamp. */
export function timeAgo(iso: string, now: number = Date.now()): string {
  const diff = Math.max(0, now - new Date(iso).getTime());
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "только что";
  if (mins < 60) return `${mins} мин назад`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} ч назад`;
  return `${Math.floor(hrs / 24)} дн назад`;
}
