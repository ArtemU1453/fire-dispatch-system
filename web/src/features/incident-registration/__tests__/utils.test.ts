import { describe, expect, it } from "vitest";
import { isValidCoord } from "../utils";
import { formatDistance, sourceLabel } from "../utils/labels";
import { nearestToSelected, recommendedToSelected } from "../utils/select";
import type { NearestResource, RecommendedUnit } from "../types";

describe("registration utils", () => {
  it("validates coordinates", () => {
    expect(isValidCoord(55.7, 37.6)).toBe(true);
    expect(isValidCoord(null, 37.6)).toBe(false);
    expect(isValidCoord(200, 37.6)).toBe(false);
  });

  it("formats distances", () => {
    expect(formatDistance(null)).toBe("—");
    expect(formatDistance(850)).toBe("850 м");
    expect(formatDistance(3200)).toBe("3.2 км");
  });

  it("localizes source labels", () => {
    expect(sourceLabel("phone")).toBe("Телефон");
  });

  it("converts a recommended unit to a selected unit", () => {
    const rec: RecommendedUnit = {
      id: "r1",
      resource_id: "u1",
      code: "АЦ-1",
      name: "Автоцистерна 1",
      role: "reserve",
      distance_meters: 500,
      score: 0.5,
      readiness: "ready",
      capabilities: [],
      reasons: ["резерв"],
      resource_type: null,
      organization: null,
    };
    const sel = recommendedToSelected(rec);
    expect(sel.resource_id).toBe("u1");
    expect(sel.role).toBe("reserve");
    expect(sel.reasons).toEqual(["резерв"]);
  });

  it("converts a nearest resource to a selected unit", () => {
    const near: NearestResource = {
      id: "u2",
      code: "АЛ-2",
      name: "Автолестница 2",
      latitude: 55.7,
      longitude: 37.6,
      distance_meters: 300,
      resource_type: "ladder",
      availability_status: "Свободен",
    };
    const sel = nearestToSelected(near);
    expect(sel.resource_id).toBe("u2");
    expect(sel.role).toBe("primary");
    expect(sel.reasons[0]).toContain("диспетчер");
  });
});
