/**
 * Operational log types.
 */

export type LogLevel = "info" | "success" | "warning" | "critical";

export type LogCategory =
  | "incident"
  | "resource"
  | "dispatch"
  | "route"
  | "system";

export interface LogEvent {
  id: string;
  occurred_at: string;
  level: LogLevel;
  category: LogCategory;
  action: string;
  message: string;
  /** Optional link back to an incident / unit. */
  incident_id?: string | null;
  unit_id?: string | null;
}
