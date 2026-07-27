/**
 * DispatchService — the AI recommendation (Dispatch Engine) for Step 4.
 * Wraps POST /dispatch/preview: a preview does not reserve resources.
 */
import { request } from "@/api/client";
import { endpoints } from "./endpoints";
import type {
  ConfidenceLevel,
  DispatchRecommendation,
  DispatchStatusOutcome,
  RecommendedUnit,
} from "../types";

export interface DispatchPreviewInput {
  incidentTypeId: string;
  latitude: number;
  longitude: number;
  address?: string | null;
  dangerLevel?: string | null;
  objectType?: string | null;
  /** Resources the dispatcher explicitly removed (re-preview). */
  excludedResourceIds?: string[];
}

interface RefLabelDto {
  id: string;
  code: string | null;
  name: string | null;
}

interface RecommendationItemDto {
  id: string;
  resource_id: string;
  code: string;
  name: string;
  role: "primary" | "reserve";
  distance_meters: number | null;
  score: number | null;
  readiness: string;
  capabilities: string[];
  reasons: string[];
  resource_type: RefLabelDto | null;
  organization: RefLabelDto | null;
}

interface RecommendationSummaryDto {
  missing_capabilities: string[];
  messages: string[];
}

interface RecommendationDto {
  status: DispatchStatusOutcome;
  sufficient: boolean;
  confidence: ConfidenceLevel;
  confidence_score: number;
  total_candidates: number;
  primary_units: RecommendationItemDto[];
  reserve_units: RecommendationItemDto[];
  summary: RecommendationSummaryDto | null;
  messages: string[];
  reasons: string[];
}

interface DispatchResponseDto {
  recommendation: RecommendationDto;
}

function mapUnit(dto: RecommendationItemDto): RecommendedUnit {
  return {
    id: dto.id,
    resource_id: dto.resource_id,
    code: dto.code,
    name: dto.name,
    role: dto.role,
    distance_meters: dto.distance_meters,
    score: dto.score,
    readiness: dto.readiness,
    capabilities: dto.capabilities,
    reasons: dto.reasons,
    resource_type: dto.resource_type?.name ?? null,
    organization: dto.organization?.name ?? null,
  };
}

export const DispatchService = {
  async preview(
    input: DispatchPreviewInput,
    signal?: AbortSignal,
  ): Promise<DispatchRecommendation> {
    const res = await request<DispatchResponseDto>({
      url: endpoints.dispatchPreview,
      method: "POST",
      data: {
        incident_type_id: input.incidentTypeId,
        latitude: input.latitude,
        longitude: input.longitude,
        address: input.address ?? undefined,
        danger_level: input.dangerLevel ?? undefined,
        object_type: input.objectType ?? undefined,
        constraints: {
          excluded_resource_ids: input.excludedResourceIds ?? [],
        },
      },
      signal,
    });
    const r = res.recommendation;
    return {
      status: r.status,
      sufficient: r.sufficient,
      confidence: r.confidence,
      confidence_score: r.confidence_score,
      total_candidates: r.total_candidates,
      primary_units: r.primary_units.map(mapUnit),
      reserve_units: r.reserve_units.map(mapUnit),
      messages: r.messages,
      reasons: r.reasons,
      missing_capabilities: r.summary?.missing_capabilities ?? [],
    };
  },
};

export type DispatchServiceType = typeof DispatchService;
