import type {
  ETAResponse,
  RecommendationItem,
  RecommendationResponse,
  ResourceSearchItem,
} from '../types/api';

export const primaryUnit: RecommendationItem = {
  id: 'item-1',
  resource_id: 'res-1',
  code: 'АЦ-1',
  name: 'Автоцистерна 1',
  role: 'primary',
  distance_meters: 1200,
  score: 0.87,
  readiness: 'deployable',
  capabilities: ['fire_suppression', 'water_supply'],
  reasons: ['Основной: подразделение доступно, имеет требуемые возможности.'],
  resource_type: { id: 't1', code: 'AC', name: 'АЦ' },
  organization: { id: 'o1', code: 'PCH1', name: 'ПЧ-1' },
  availability_status: { id: 's1', code: 'avail', name: 'Свободен' },
};

export const reserveUnit: RecommendationItem = {
  ...primaryUnit,
  id: 'item-2',
  resource_id: 'res-2',
  code: 'АЦ-2',
  name: 'Автоцистерна 2',
  role: 'reserve',
  distance_meters: 3400,
};

export const recommendation: RecommendationResponse = {
  id: 'inc-1',
  incident_id: 'inc-1',
  incident_type_id: 'type-1',
  complexity: 'moderate',
  point: { latitude: 55.75, longitude: 37.62 },
  address: 'ул. Тверская, 1',
  priority: 'high',
  status: 'recommended',
  sufficient: true,
  confidence: 'high',
  confidence_score: 0.82,
  total_candidates: 4,
  is_preview: false,
  required_capabilities: [
    { code: 'fire_suppression', min_quantity: 1, mandatory: true, label: 'Пожаротушение' },
  ],
  primary_units: [primaryUnit],
  reserve_units: [reserveUnit],
  capability_coverage: [
    {
      code: 'fire_suppression',
      label: 'Пожаротушение',
      required: 1,
      provided: 1,
      satisfied: true,
      mandatory: true,
    },
  ],
  resource_matches: [],
  summary: {
    primary_count: 1,
    reserve_count: 1,
    minimum_units: 1,
    recommended_units: 2,
    reserve_units: 1,
    required_capabilities: ['fire_suppression'],
    covered_capabilities: ['fire_suppression'],
    missing_capabilities: [],
    messages: ['Рекомендация сформирована; требования выполнены.'],
  },
  messages: ['Рекомендация сформирована; требования выполнены.'],
  reasons: ['Покрыты возможности: fire_suppression.'],
  rule_codes: ['FIRE-BASIC'],
  created_at: '2026-07-25T18:00:00Z',
};

export const eta: ETAResponse = {
  origin: { latitude: 55.75, longitude: 37.62 },
  destination: { latitude: 55.76, longitude: 37.63 },
  eta_seconds: 300,
  eta_minutes: 5,
  distance_meters: 1200,
  provider: 'haversine',
  is_fallback: false,
};

export const resourceItem: ResourceSearchItem = {
  id: 'res-1',
  code: 'АЦ-1',
  name: 'Автоцистерна 1',
  is_active: true,
  latitude: 55.76,
  longitude: 37.63,
  distance_meters: 1200,
  resource_type: { id: 't1', code: 'AC', name: 'АЦ', category: 'vehicle' },
  organization: { id: 'o1', code: 'PCH1', name: 'ПЧ-1' },
  availability_status: { id: 's1', code: 'avail', name: 'Свободен' },
  specialization: null,
};
