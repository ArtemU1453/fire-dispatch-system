/**
 * TypeScript types mirroring the backend API contracts.
 *
 * These are hand-written to match the backend OpenAPI schemas. The frontend is a
 * pure client — it never embeds business logic; it only shapes requests and
 * renders responses.
 */

// ------------------------------------------------------------------ health ---
export interface HealthStatus {
  status: string;
  app: string;
  version: string;
  environment: string;
  database?: string | null;
}

export interface ProviderHealth {
  provider: string;
  healthy: boolean;
  detail?: string | null;
  latency_ms?: number | null;
}

// ----------------------------------------------------------------- geocode ---
export interface GeocodeResult {
  formatted_address: string;
  normalized_address?: string | null;
  latitude: number;
  longitude: number;
  accuracy: string;
  source: string;
}

export interface GeocodeResponse {
  query: string;
  normalized_address?: string | null;
  provider: string;
  from_cache: boolean;
  success: boolean;
  error?: string | null;
  count: number;
  results: GeocodeResult[];
}

// ------------------------------------------------------------------ search ---
export interface RefLabel {
  id: string;
  code?: string | null;
  name?: string | null;
}

export interface ResourceTypeRef {
  id: string;
  code?: string | null;
  name?: string | null;
  category?: string | null;
}

export interface ResourceSearchItem {
  id: string;
  code: string;
  name: string;
  is_active: boolean;
  latitude?: number | null;
  longitude?: number | null;
  distance_meters?: number | null;
  resource_type?: ResourceTypeRef | null;
  organization?: RefLabel | null;
  availability_status?: RefLabel | null;
  specialization?: string | null;
}

export interface SearchResponse {
  total: number;
  limit: number;
  offset: number;
  count: number;
  reference_point?: { latitude: number; longitude: number } | null;
  from_cache: boolean;
  items: ResourceSearchItem[];
}

// ---------------------------------------------------------------- dispatch ---
export type RecommendationRole = 'primary' | 'reserve';
export type DispatchStatus = 'recommended' | 'partial' | 'no_resources';
export type ConfidenceLevel = 'low' | 'medium' | 'high';
export type IncidentComplexity = 'simple' | 'moderate' | 'complex' | 'critical';
export type RulePriority = 'low' | 'normal' | 'high' | 'critical';

export interface DispatchConstraints {
  organization_ids?: string[];
  excluded_resource_ids?: string[];
  radius_meters?: number | null;
  time_of_day_hour?: number | null;
}

export interface DispatchRequest {
  incident_id?: string | null;
  incident_type_id: string;
  complexity?: IncidentComplexity | null;
  latitude?: number | null;
  longitude?: number | null;
  address?: string | null;
  administrative_area_id?: string | null;
  danger_level?: string | null;
  object_type?: string | null;
  flags?: string[];
  constraints?: DispatchConstraints;
}

export interface CapabilityResponse {
  code: string;
  min_quantity: number;
  mandatory: boolean;
  label?: string | null;
}

export interface CapabilityCoverageItem {
  code: string;
  label?: string | null;
  required: number;
  provided: number;
  satisfied: boolean;
  mandatory: boolean;
}

export interface RecommendationItem {
  id: string;
  resource_id: string;
  code: string;
  name: string;
  role: RecommendationRole;
  distance_meters?: number | null;
  score?: number | null;
  readiness: string;
  capabilities: string[];
  reasons: string[];
  resource_type?: RefLabel | null;
  organization?: RefLabel | null;
  availability_status?: RefLabel | null;
}

export interface ResourceMatchResponse {
  resource_id: string;
  code: string;
  name: string;
  distance_meters?: number | null;
  score?: number | null;
  readiness: string;
  selected: boolean;
  excluded: boolean;
  exclusion_reason?: string | null;
  detail?: string | null;
}

export interface RecommendationSummaryResponse {
  primary_count: number;
  reserve_count: number;
  minimum_units: number;
  recommended_units: number;
  reserve_units: number;
  required_capabilities: string[];
  covered_capabilities: string[];
  missing_capabilities: string[];
  messages: string[];
}

export interface DispatchPoint {
  latitude: number;
  longitude: number;
}

export interface RecommendationResponse {
  id: string;
  incident_id?: string | null;
  incident_type_id: string;
  complexity?: IncidentComplexity | null;
  point: DispatchPoint;
  address?: string | null;
  priority: RulePriority;
  status: DispatchStatus;
  sufficient: boolean;
  confidence: ConfidenceLevel;
  confidence_score: number;
  total_candidates: number;
  is_preview: boolean;
  required_capabilities: CapabilityResponse[];
  primary_units: RecommendationItem[];
  reserve_units: RecommendationItem[];
  capability_coverage: CapabilityCoverageItem[];
  resource_matches: ResourceMatchResponse[];
  summary?: RecommendationSummaryResponse | null;
  messages: string[];
  reasons: string[];
  rule_codes: string[];
  created_at?: string | null;
}

export interface DispatchResponse {
  recommendation: RecommendationResponse;
}

// ----------------------------------------------------------------- routing ---
export type TravelProfile = 'driving' | 'walking' | 'cycling';

export interface RoutePointOut {
  latitude: number;
  longitude: number;
  name?: string | null;
  is_waypoint: boolean;
}

export interface RouteSegmentOut {
  distance_meters: number;
  duration_seconds: number;
}

export interface RouteResponse {
  origin: RoutePointOut;
  destination: RoutePointOut;
  distance_meters: number;
  distance_km: number;
  duration_seconds: number;
  eta_minutes: number;
  provider: string;
  profile: TravelProfile;
  is_fallback: boolean;
  response_time_ms: number;
  waypoints: RoutePointOut[];
  segments: RouteSegmentOut[];
  geometry: RoutePointOut[];
}

export interface ETAResponse {
  origin: DispatchPoint;
  destination: DispatchPoint;
  eta_seconds: number;
  eta_minutes: number;
  distance_meters: number;
  provider: string;
  is_fallback: boolean;
}

export interface DistanceResponse {
  origin: DispatchPoint;
  destination: DispatchPoint;
  distance_meters: number;
  distance_km: number;
  provider: string;
  is_fallback: boolean;
}

// ------------------------------------------------------------------- rules ---
export interface IncidentTypeOption {
  id: string;
  code: string;
  name: string;
}
