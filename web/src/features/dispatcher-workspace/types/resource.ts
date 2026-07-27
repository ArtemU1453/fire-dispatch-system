/**
 * Resource (units / vehicles / crews) domain types, mirroring the backend
 * `app.resources` schemas.
 */

export interface StatusRef {
  id: string;
  code: string;
  name: string;
  is_operational: boolean;
  is_available_for_dispatch: boolean;
  color: string | null;
}

export interface RefLabel {
  id: string;
  code: string | null;
  name: string | null;
}

export interface Unit {
  id: string;
  code: string;
  name: string;
  call_sign: string | null;
  station_id: string | null;
  organization: RefLabel | null;
  vehicle_resource_id: string | null;
  status: StatusRef | null;
  is_active: boolean;
  is_available: boolean;
  crew_count: number;
  active_assignment_id: string | null;
  notes: string | null;
}

export interface Vehicle {
  resource_id: string;
  code: string;
  name: string;
  plate_number: string | null;
  vehicle_type: RefLabel | null;
  status: StatusRef | null;
  is_available: boolean;
  fuel_level_percent: number | null;
}

export interface StatusOverviewItem {
  status: StatusRef;
  resource_count: number;
}

/** A resource position as returned by `/units/{id}/location`. */
export interface Position {
  resource_id: string;
  latitude: number;
  longitude: number;
  recorded_at: string | null;
  source: string;
}

/** A unit enriched with its live position for the map. */
export interface UnitWithPosition extends Unit {
  position: Position | null;
}
