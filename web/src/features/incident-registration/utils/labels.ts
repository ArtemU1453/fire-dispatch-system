/**
 * Russian labels for the registration form. Category / priority labels and the
 * ETA formatter are reused from the dispatcher-workspace feature (DRY).
 */
export {
  CATEGORY_LABELS,
  PRIORITY_LABELS,
  categoryLabel,
  priorityLabel,
  priorityVariant,
  formatEta,
} from "@/features/dispatcher-workspace/utils/format";

import type { ConfidenceLevel, IncidentSource } from "../types";

export const SOURCE_LABELS: Record<IncidentSource, string> = {
  phone: "Телефон",
  radio: "Радиосвязь",
  system: "Система",
  patrol: "Патруль",
  manual: "Ручной ввод",
  other: "Другое",
};

export const CONFIDENCE_LABELS: Record<ConfidenceLevel, string> = {
  low: "Низкая",
  medium: "Средняя",
  high: "Высокая",
};

export function sourceLabel(source: IncidentSource): string {
  return SOURCE_LABELS[source] ?? source;
}

/** Distance in metres → compact ru string ("850 м", "3.2 км"). */
export function formatDistance(meters: number | null | undefined): string {
  if (meters == null || Number.isNaN(meters)) return "—";
  if (meters < 1000) return `${Math.round(meters)} м`;
  return `${(meters / 1000).toFixed(1)} км`;
}
