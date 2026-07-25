/**
 * Incident-draft store — the dispatcher's working call card and UI selection.
 *
 * Holds only *input* and *UI* state (the call being composed, the map view, the
 * selected units, the confirmed composition). All *server* data (geocoding,
 * recommendations, routes) lives in React Query — never duplicated here.
 */
import { create } from 'zustand';

export interface IncidentDraft {
  callNumber: string;
  incidentTypeId: string;
  incidentTypeLabel: string;
  complexity: string;
  address: string;
  latitude: number | null;
  longitude: number | null;
  dangerLevel: string;
  objectType: string;
  extraInfo: string;
}

const emptyDraft: IncidentDraft = {
  callNumber: '',
  incidentTypeId: '',
  incidentTypeLabel: '',
  complexity: '',
  address: '',
  latitude: null,
  longitude: null,
  dangerLevel: '',
  objectType: '',
  extraInfo: '',
};

interface IncidentState {
  draft: IncidentDraft;
  /** id of the persisted recommendation currently displayed (React Query key). */
  incidentId: string | null;
  selectedUnitIds: string[];
  confirmed: boolean;
  searchRadius: number;
  mapFocus: { lat: number; lon: number } | null;

  setDraftField: <K extends keyof IncidentDraft>(
    key: K,
    value: IncidentDraft[K],
  ) => void;
  setCoordinates: (lat: number, lon: number, address?: string) => void;
  setIncidentType: (id: string, label: string) => void;
  setIncidentId: (id: string | null) => void;
  toggleUnit: (resourceId: string) => void;
  setSelectedUnits: (ids: string[]) => void;
  confirmComposition: () => void;
  setSearchRadius: (meters: number) => void;
  focusMap: (lat: number, lon: number) => void;
  reset: () => void;
}

export const useIncidentStore = create<IncidentState>((set) => ({
  draft: emptyDraft,
  incidentId: null,
  selectedUnitIds: [],
  confirmed: false,
  searchRadius: 15000,
  mapFocus: null,

  setDraftField: (key, value) =>
    set((state) => ({ draft: { ...state.draft, [key]: value } })),
  setCoordinates: (lat, lon, address) =>
    set((state) => ({
      draft: {
        ...state.draft,
        latitude: lat,
        longitude: lon,
        address: address ?? state.draft.address,
      },
      mapFocus: { lat, lon },
    })),
  setIncidentType: (id, label) =>
    set((state) => ({
      draft: { ...state.draft, incidentTypeId: id, incidentTypeLabel: label },
    })),
  setIncidentId: (id) => set({ incidentId: id, confirmed: false }),
  toggleUnit: (resourceId) =>
    set((state) => ({
      selectedUnitIds: state.selectedUnitIds.includes(resourceId)
        ? state.selectedUnitIds.filter((id) => id !== resourceId)
        : [...state.selectedUnitIds, resourceId],
      confirmed: false,
    })),
  setSelectedUnits: (ids) => set({ selectedUnitIds: ids, confirmed: false }),
  confirmComposition: () => set({ confirmed: true }),
  setSearchRadius: (meters) => set({ searchRadius: meters }),
  focusMap: (lat, lon) => set({ mapFocus: { lat, lon } }),
  reset: () =>
    set({
      draft: emptyDraft,
      incidentId: null,
      selectedUnitIds: [],
      confirmed: false,
      mapFocus: null,
    }),
}));
