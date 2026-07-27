import { describe, expect, it } from "vitest";
import {
  buildIncidentPoints,
  buildStraightRoute,
  buildUnitPoints,
} from "../services/map-features.service";
import type { Incident } from "../types";
import type { SpatialObject } from "../api/map.service";

function incident(partial: Partial<Incident>): Incident {
  return {
    id: "i1",
    number: "0001",
    category: "fire",
    source: "phone",
    status: "confirmed",
    priority: "high",
    title: null,
    description: null,
    address: "ул. Тестовая, 1",
    latitude: 55.75,
    longitude: 37.61,
    danger_level: null,
    object_type: null,
    reporter_name: null,
    reporter_contact: null,
    reported_at: "2026-07-27T10:00:00Z",
    confirmed_at: null,
    closed_at: null,
    allowed_transitions: [],
    locations: [],
    comments: [],
    timeline: [],
    dispatches: [],
    ...partial,
  };
}

describe("map feature builders", () => {
  it("builds incident points and skips invalid coordinates", () => {
    const points = buildIncidentPoints([
      incident({ id: "a" }),
      incident({ id: "b", latitude: null, longitude: null }),
    ]);
    expect(points).toHaveLength(1);
    expect(points[0].id).toBe("incident:a");
    expect(points[0].kind).toBe("incident");
    expect(points[0].priority).toBe("high");
  });

  it("builds unit points from spatial objects", () => {
    const objects: SpatialObject[] = [
      { id: "u1", code: "АЦ-1", name: "Автоцистерна 1", latitude: 55.7, longitude: 37.6 },
      { id: "u2", code: null, name: null, latitude: null, longitude: null },
    ];
    const points = buildUnitPoints(objects);
    expect(points).toHaveLength(1);
    expect(points[0].kind).toBe("unit");
    expect(points[0].available).toBe(true);
  });

  it("builds a straight route between two valid points", () => {
    const route = buildStraightRoute(
      "r1",
      "маршрут",
      { latitude: 55.7, longitude: 37.6 },
      { latitude: 55.8, longitude: 37.7 },
    );
    expect(route).not.toBeNull();
    expect(route?.coordinates).toHaveLength(2);
  });

  it("returns null for an invalid straight route", () => {
    const route = buildStraightRoute(
      "r1",
      "маршрут",
      { latitude: NaN, longitude: 37.6 },
      { latitude: 55.8, longitude: 37.7 },
    );
    expect(route).toBeNull();
  });
});
