/**
 * DispatcherStore — client-only UI state for the workspace (selection, map
 * settings, filters). Server data lives in TanStack Query, never here. Map
 * preferences and filters are persisted so a dispatcher's layout survives a
 * reload; the volatile selection is intentionally not persisted.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type {
  IncidentCategory,
  IncidentPriority,
  IncidentStatus,
  MapLayerId,
  MapLayerVisibility,
} from "../types";
import { DEFAULT_CENTER, DEFAULT_ZOOM } from "../utils/geo";

export type IncidentSortKey = "reported_desc" | "reported_asc" | "priority";

export interface IncidentFilters {
  search: string;
  statuses: IncidentStatus[];
  priorities: IncidentPriority[];
  categories: IncidentCategory[];
  sort: IncidentSortKey;
}

export interface MapSettings {
  center: { longitude: number; latitude: number };
  zoom: number;
  layers: MapLayerVisibility;
}

const DEFAULT_LAYERS: MapLayerVisibility = {
  incidents: true,
  units: true,
  routes: true,
  zones: false,
  hydrants: false,
  water_sources: false,
  closed_roads: false,
};

const DEFAULT_FILTERS: IncidentFilters = {
  search: "",
  statuses: [],
  priorities: [],
  categories: [],
  sort: "reported_desc",
};

interface DispatcherState {
  selectedIncidentId: string | null;
  selectedUnitId: string | null;
  filters: IncidentFilters;
  map: MapSettings;
  /** Incident the map should fly to (consumed once, then cleared). */
  flyToIncidentId: string | null;

  selectIncident: (id: string | null) => void;
  selectUnit: (id: string | null) => void;
  setFilters: (patch: Partial<IncidentFilters>) => void;
  resetFilters: () => void;
  toggleLayer: (layer: MapLayerId) => void;
  setLayer: (layer: MapLayerId, visible: boolean) => void;
  setMapView: (center: { longitude: number; latitude: number }, zoom: number) => void;
  requestFlyTo: (incidentId: string) => void;
  clearFlyTo: () => void;
}

export const useDispatcherStore = create<DispatcherState>()(
  persist(
    (set) => ({
      selectedIncidentId: null,
      selectedUnitId: null,
      filters: DEFAULT_FILTERS,
      map: { center: DEFAULT_CENTER, zoom: DEFAULT_ZOOM, layers: DEFAULT_LAYERS },
      flyToIncidentId: null,

      selectIncident: (id) => set({ selectedIncidentId: id, selectedUnitId: null }),
      selectUnit: (id) => set({ selectedUnitId: id }),
      setFilters: (patch) =>
        set((s) => ({ filters: { ...s.filters, ...patch } })),
      resetFilters: () => set({ filters: DEFAULT_FILTERS }),
      toggleLayer: (layer) =>
        set((s) => ({
          map: {
            ...s.map,
            layers: { ...s.map.layers, [layer]: !s.map.layers[layer] },
          },
        })),
      setLayer: (layer, visible) =>
        set((s) => ({
          map: { ...s.map, layers: { ...s.map.layers, [layer]: visible } },
        })),
      setMapView: (center, zoom) =>
        set((s) => ({ map: { ...s.map, center, zoom } })),
      requestFlyTo: (incidentId) =>
        set({ flyToIncidentId: incidentId, selectedIncidentId: incidentId }),
      clearFlyTo: () => set({ flyToIncidentId: null }),
    }),
    {
      name: "aid.dispatcher",
      // Persist layout preferences only; selection & fly-to stay volatile.
      partialize: (s) => ({ filters: s.filters, map: s.map }),
    },
  ),
);
