/**
 * IncidentRegistrationStore — client state for the registration workflow.
 *
 * Holds the in-progress form, the resolved location, the Dispatch Engine
 * recommendation and the dispatcher's selected units (in send order). Server
 * fetches (address search, preview) live in TanStack Query; this store is the
 * workflow's own volatile state and is intentionally not persisted.
 */
import { create } from "zustand";
import type {
  DispatchRecommendation,
  RecommendedUnit,
  RegistrationStatus,
  ResolvedLocation,
  SelectedUnit,
} from "../types";
import {
  defaultIncidentFormValues,
  type IncidentFormValues,
} from "../validation/incidentForm.schema";

function toSelected(unit: RecommendedUnit): SelectedUnit {
  return {
    resource_id: unit.resource_id,
    code: unit.code,
    name: unit.name,
    role: unit.role,
    distance_meters: unit.distance_meters,
    eta_seconds: unit.eta_seconds ?? null,
    reasons: unit.reasons,
  };
}

interface RegistrationState {
  status: RegistrationStatus;
  error: string | null;

  form: IncidentFormValues;
  location: ResolvedLocation | null;
  recommendation: DispatchRecommendation | null;
  selectedUnits: SelectedUnit[];
  excludedResourceIds: string[];
  createdIncidentId: string | null;
  createdIncidentNumber: string | null;

  setStatus: (status: RegistrationStatus, error?: string | null) => void;
  setForm: (form: IncidentFormValues) => void;
  setLocation: (location: ResolvedLocation | null) => void;
  applyRecommendation: (rec: DispatchRecommendation) => void;

  addUnit: (unit: SelectedUnit) => void;
  removeUnit: (resourceId: string) => void;
  moveUnit: (resourceId: string, direction: -1 | 1) => void;

  setCreated: (id: string, number: string) => void;
  reset: () => void;
}

const initial = {
  status: "draft" as RegistrationStatus,
  error: null,
  form: defaultIncidentFormValues,
  location: null,
  recommendation: null,
  selectedUnits: [] as SelectedUnit[],
  excludedResourceIds: [] as string[],
  createdIncidentId: null,
  createdIncidentNumber: null,
};

export const useRegistrationStore = create<RegistrationState>((set) => ({
  ...initial,

  setStatus: (status, error = null) => set({ status, error }),
  setForm: (form) => set({ form }),
  setLocation: (location) => set({ location }),

  applyRecommendation: (rec) =>
    set(() => ({
      recommendation: rec,
      // Preselect the primary units in the engine's order.
      selectedUnits: rec.primary_units.map(toSelected),
      status: "recommended",
      error: null,
    })),

  addUnit: (unit) =>
    set((s) => {
      if (s.selectedUnits.some((u) => u.resource_id === unit.resource_id)) return s;
      return {
        selectedUnits: [...s.selectedUnits, unit],
        excludedResourceIds: s.excludedResourceIds.filter(
          (id) => id !== unit.resource_id,
        ),
      };
    }),

  removeUnit: (resourceId) =>
    set((s) => ({
      selectedUnits: s.selectedUnits.filter((u) => u.resource_id !== resourceId),
      excludedResourceIds: s.excludedResourceIds.includes(resourceId)
        ? s.excludedResourceIds
        : [...s.excludedResourceIds, resourceId],
    })),

  moveUnit: (resourceId, direction) =>
    set((s) => {
      const idx = s.selectedUnits.findIndex((u) => u.resource_id === resourceId);
      const next = idx + direction;
      if (idx < 0 || next < 0 || next >= s.selectedUnits.length) return s;
      const units = [...s.selectedUnits];
      [units[idx], units[next]] = [units[next], units[idx]];
      return { selectedUnits: units };
    }),

  setCreated: (id, number) =>
    set({ createdIncidentId: id, createdIncidentNumber: number }),

  reset: () => set({ ...initial }),
}));
