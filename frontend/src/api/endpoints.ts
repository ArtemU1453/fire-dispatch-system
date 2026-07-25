/**
 * Typed endpoint functions over the shared axios client.
 *
 * Each function maps 1:1 to an existing backend route. No business logic lives
 * here — requests in, typed responses out.
 */
import { apiClient } from './client';
import type {
  DispatchRequest,
  DispatchResponse,
  DistanceResponse,
  ETAResponse,
  GeocodeResponse,
  HealthStatus,
  ProviderHealth,
  RecommendationResponse,
  ResourceSearchItem,
  RouteResponse,
  SearchResponse,
  TravelProfile,
} from '../types/api';

// ------------------------------------------------------------------ health ---
export async function getHealth(): Promise<HealthStatus> {
  const { data } = await apiClient.get<HealthStatus>('/health');
  return data;
}

export async function getRoutingHealth(): Promise<ProviderHealth> {
  const { data } = await apiClient.get<ProviderHealth>('/routing/health');
  return data;
}

// ----------------------------------------------------------------- geocode ---
export async function geocode(query: string, limit = 5): Promise<GeocodeResponse> {
  const { data } = await apiClient.get<GeocodeResponse>('/geocode', {
    params: { q: query, limit },
  });
  return data;
}

// ------------------------------------------------------------------ search ---
export interface ResourceSearchParams {
  lat?: number;
  lon?: number;
  radius_m?: number;
  categories?: string[];
  limit?: number;
  q?: string;
  deployable?: boolean;
}

export async function searchResources(
  params: ResourceSearchParams,
): Promise<SearchResponse> {
  const { data } = await apiClient.get<SearchResponse>('/resources/search', {
    params,
  });
  return data;
}

export async function getResource(resourceId: string): Promise<ResourceSearchItem> {
  const { data } = await apiClient.get<ResourceSearchItem>(
    `/resources/${resourceId}`,
  );
  return data;
}

// ---------------------------------------------------------------- dispatch ---
export async function recommend(
  request: DispatchRequest,
  preview = false,
): Promise<RecommendationResponse> {
  const path = preview ? '/dispatch/preview' : '/dispatch/recommend';
  const { data } = await apiClient.post<DispatchResponse>(path, request);
  return data.recommendation;
}

export async function getRecommendation(
  incidentId: string,
): Promise<RecommendationResponse> {
  const { data } = await apiClient.get<RecommendationResponse>(
    `/dispatch/${incidentId}`,
  );
  return data;
}

// ----------------------------------------------------------------- routing ---
export interface LatLon {
  lat: number;
  lon: number;
}

export async function buildRoute(
  origin: LatLon,
  destination: LatLon,
  profile: TravelProfile = 'driving',
): Promise<RouteResponse> {
  const { data } = await apiClient.get<RouteResponse>('/routing/route', {
    params: {
      from_lat: origin.lat,
      from_lon: origin.lon,
      to_lat: destination.lat,
      to_lon: destination.lon,
      profile,
    },
  });
  return data;
}

export async function estimateEta(
  origin: LatLon,
  destination: LatLon,
): Promise<ETAResponse> {
  const { data } = await apiClient.post<ETAResponse>('/routing/eta', {
    origin: { latitude: origin.lat, longitude: origin.lon },
    destination: { latitude: destination.lat, longitude: destination.lon },
  });
  return data;
}

export async function computeDistance(
  origin: LatLon,
  destination: LatLon,
): Promise<DistanceResponse> {
  const { data } = await apiClient.post<DistanceResponse>('/routing/distance', {
    origin: { latitude: origin.lat, longitude: origin.lon },
    destination: { latitude: destination.lat, longitude: destination.lon },
  });
  return data;
}

// ------------------------------------------------------------------- rules ---
interface RuleSummary {
  id: string;
  code: string;
  name: string;
}
interface RuleDetail {
  id: string;
  name: string;
  incident_type_ids: string[];
}

export async function listRules(): Promise<RuleSummary[]> {
  const { data } = await apiClient.get<RuleSummary[]>('/rules', {
    params: { enabled_only: true, limit: 200 },
  });
  return data;
}

export async function getRule(ruleId: string): Promise<RuleDetail> {
  const { data } = await apiClient.get<RuleDetail>(`/rules/${ruleId}`);
  return data;
}
