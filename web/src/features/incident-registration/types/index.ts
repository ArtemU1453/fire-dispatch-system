/**
 * Domain types for the incident-registration workflow. Enum types are reused
 * from the dispatcher-workspace feature to avoid duplication.
 */
export type {
  IncidentCategory,
  IncidentPriority,
  IncidentSource,
} from "@/features/dispatcher-workspace/types";

/** Confidence of the AI recommendation. */
export type ConfidenceLevel = "low" | "medium" | "high";
export type DispatchStatusOutcome = "recommended" | "partial" | "no_resources";
export type RecommendationRole = "primary" | "reserve";

/** A geocoding result (from GET /geocode). */
export interface AddressCandidate {
  /** Stable client id (no server id on geocode results). */
  id: string;
  formatted_address: string;
  normalized_address: string | null;
  latitude: number;
  longitude: number;
  accuracy: string;
  source: string;
}

/** Address components resolved via reverse geocoding. */
export interface ResolvedArea {
  region: string | null;
  district: string | null;
  settlement: string | null;
  street: string | null;
  house_number: string | null;
  formatted_address: string | null;
}

/** The fully-resolved location the registration works with. */
export interface ResolvedLocation {
  address: string;
  latitude: number;
  longitude: number;
  area: ResolvedArea | null;
}

/** An incident-type catalog item. */
export interface IncidentTypeOption {
  id: string;
  code: string;
  name: string;
}

/** A nearby resource returned by GET /resources/nearest. */
export interface NearestResource {
  id: string;
  code: string;
  name: string;
  latitude: number | null;
  longitude: number | null;
  distance_meters: number | null;
  resource_type: string | null;
  availability_status: string | null;
}

/** A recommended unit from the Dispatch Engine (POST /dispatch/preview). */
export interface RecommendedUnit {
  id: string;
  resource_id: string;
  code: string;
  name: string;
  role: RecommendationRole;
  distance_meters: number | null;
  score: number | null;
  readiness: string;
  capabilities: string[];
  reasons: string[];
  resource_type: string | null;
  organization: string | null;
  eta_seconds?: number | null;
}

/** The recommendation envelope surfaced to the UI. */
export interface DispatchRecommendation {
  status: DispatchStatusOutcome;
  sufficient: boolean;
  confidence: ConfidenceLevel;
  confidence_score: number;
  total_candidates: number;
  primary_units: RecommendedUnit[];
  reserve_units: RecommendedUnit[];
  messages: string[];
  reasons: string[];
  missing_capabilities: string[];
}

/** A unit the dispatcher has chosen to send, in send order. */
export interface SelectedUnit {
  resource_id: string;
  code: string;
  name: string;
  role: RecommendationRole;
  distance_meters: number | null;
  eta_seconds: number | null;
  /** Why the engine recommended it (empty when manually added). */
  reasons: string[];
}

/** The lifecycle of the registration process. */
export type RegistrationStatus =
  | "draft" // filling the form
  | "locating" // resolving address
  | "located" // address resolved, coordinates known
  | "recommending" // awaiting Dispatch Engine
  | "recommended" // recommendation received
  | "confirming" // confirmation modal open
  | "submitting" // creating incident + assigning units
  | "submitted" // done
  | "error";
