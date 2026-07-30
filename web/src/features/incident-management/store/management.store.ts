/**
 * IncidentManagementStore — client-only UI state for the management screen.
 * Server data (incident, resources, timeline) lives in TanStack Query; this
 * store holds selection, filters and map view for one incident session.
 */
import { create } from "zustand";
import type { TimelineCategory } from "../types";

export type ManagementLayerId =
  | "incident"
  | "routes"
  | "units"
  | "coverage"
  | "hydrants"
  | "water_sources"
  | "closed_roads"
  | "hazard_zones"
  | "district";

export type ManagementLayers = Record<ManagementLayerId, boolean>;

interface TimelineFilters {
  search: string;
  category: TimelineCategory;
}

interface MapView {
  center: { longitude: number; latitude: number } | null;
  zoom: number;
  layers: ManagementLayers;
}

const DEFAULT_LAYERS: ManagementLayers = {
  incident: true,
  routes: true,
  units: true,
  coverage: true,
  hydrants: false,
  water_sources: false,
  closed_roads: false,
  hazard_zones: false,
  district: false,
};

interface ManagementState {
  incidentId: string | null;
  selectedResourceId: string | null;
  timeline: TimelineFilters;
  map: MapView;

  setIncidentId: (id: string | null) => void;
  selectResource: (resourceId: string | null) => void;
  setTimelineFilters: (patch: Partial<TimelineFilters>) => void;
  toggleLayer: (layer: ManagementLayerId) => void;
  setMapView: (center: { longitude: number; latitude: number }, zoom: number) => void;
  reset: () => void;
}

const initialMap: MapView = { center: null, zoom: 13, layers: DEFAULT_LAYERS };

export const useManagementStore = create<ManagementState>((set) => ({
  incidentId: null,
  selectedResourceId: null,
  timeline: { search: "", category: "all" },
  map: initialMap,

  setIncidentId: (id) => set({ incidentId: id }),
  selectResource: (resourceId) => set({ selectedResourceId: resourceId }),
  setTimelineFilters: (patch) =>
    set((s) => ({ timeline: { ...s.timeline, ...patch } })),
  toggleLayer: (layer) =>
    set((s) => ({
      map: { ...s.map, layers: { ...s.map.layers, [layer]: !s.map.layers[layer] } },
    })),
  setMapView: (center, zoom) => set((s) => ({ map: { ...s.map, center, zoom } })),
  reset: () =>
    set({
      selectedResourceId: null,
      timeline: { search: "", category: "all" },
      map: { ...initialMap, center: null },
    }),
}));
