/**
 * Domain types for operational incident management. Core incident / timeline /
 * dispatch types are reused from the dispatcher-workspace feature.
 */
export type {
  Incident,
  IncidentStatus,
  IncidentPriority,
  IncidentCategory,
  IncidentSource,
  DispatchUnit,
  DispatchUnitStatus,
  TimelineEntry,
  IncidentTimeline,
} from "@/features/dispatcher-workspace/types";

/** A seeded availability status (from GET /resources/status). */
export interface UnitStatusOption {
  code: string;
  name: string;
  color: string | null;
  isAvailableForDispatch: boolean;
}

/**
 * A resource assigned to the incident, composed from the incident's dispatch
 * records enriched with live unit metadata (name, vehicle, crew, status).
 */
export interface AssignedResource {
  /** The dispatch record's resource id (as stored on the incident). */
  resourceId: string;
  /** The matched unit id (for unit-centric actions), null if unmatched. */
  unitId: string | null;
  code: string;
  name: string;
  callSign: string | null;
  role: string;
  /** Incident-side dispatch status. */
  dispatchStatus: string;
  /** Live availability status of the unit. */
  unitStatus: UnitStatusOption | null;
  vehicleType: string | null;
  crewCount: number;
  assignedAt: string;
  departedAt: string | null;
  arrivedAt: string | null;
  etaSeconds: number | null;
  /** Current speed in km/h, when the position feed provides it (else null). */
  speedKmh: number | null;
}

/** Timeline filter category. */
export type TimelineCategory =
  | "all"
  | "registration"
  | "assignment"
  | "status"
  | "route"
  | "message"
  | "decision";

/** Quick-action identifiers for the operational toolbar. */
export type QuickActionId =
  | "add_resource"
  | "change_level"
  | "transfer"
  | "message"
  | "print"
  | "close";
