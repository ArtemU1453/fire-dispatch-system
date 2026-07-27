import { beforeEach, describe, expect, it } from "vitest";
import { useRegistrationStore } from "../store/registration.store";
import type { DispatchRecommendation, RecommendedUnit, SelectedUnit } from "../types";

function unit(id: string, role: "primary" | "reserve" = "primary"): RecommendedUnit {
  return {
    id: `rec-${id}`,
    resource_id: id,
    code: `АЦ-${id}`,
    name: `Автоцистерна ${id}`,
    role,
    distance_meters: 1200,
    score: 0.9,
    readiness: "ready",
    capabilities: [],
    reasons: ["ближайшее"],
    resource_type: null,
    organization: null,
  };
}

function selected(id: string): SelectedUnit {
  return {
    resource_id: id,
    code: `АЦ-${id}`,
    name: `Автоцистерна ${id}`,
    role: "primary",
    distance_meters: 900,
    eta_seconds: null,
    reasons: [],
  };
}

const recommendation: DispatchRecommendation = {
  status: "recommended",
  sufficient: true,
  confidence: "high",
  confidence_score: 0.88,
  total_candidates: 5,
  primary_units: [unit("a"), unit("b")],
  reserve_units: [unit("c", "reserve")],
  messages: [],
  reasons: [],
  missing_capabilities: [],
};

describe("IncidentRegistrationStore", () => {
  beforeEach(() => useRegistrationStore.getState().reset());

  it("preselects primary units when a recommendation is applied", () => {
    useRegistrationStore.getState().applyRecommendation(recommendation);
    const s = useRegistrationStore.getState();
    expect(s.status).toBe("recommended");
    expect(s.selectedUnits.map((u) => u.resource_id)).toEqual(["a", "b"]);
  });

  it("removing a unit records it as excluded", () => {
    useRegistrationStore.getState().applyRecommendation(recommendation);
    useRegistrationStore.getState().removeUnit("a");
    const s = useRegistrationStore.getState();
    expect(s.selectedUnits.map((u) => u.resource_id)).toEqual(["b"]);
    expect(s.excludedResourceIds).toContain("a");
  });

  it("adds a unit and clears it from excluded", () => {
    useRegistrationStore.getState().removeUnit("x"); // excludes x
    useRegistrationStore.getState().addUnit(selected("x"));
    const s = useRegistrationStore.getState();
    expect(s.selectedUnits.some((u) => u.resource_id === "x")).toBe(true);
    expect(s.excludedResourceIds).not.toContain("x");
  });

  it("does not add a duplicate unit", () => {
    useRegistrationStore.getState().addUnit(selected("a"));
    useRegistrationStore.getState().addUnit(selected("a"));
    expect(useRegistrationStore.getState().selectedUnits).toHaveLength(1);
  });

  it("reorders the send order", () => {
    useRegistrationStore.getState().applyRecommendation(recommendation);
    useRegistrationStore.getState().moveUnit("b", -1);
    expect(
      useRegistrationStore.getState().selectedUnits.map((u) => u.resource_id),
    ).toEqual(["b", "a"]);
  });
});
