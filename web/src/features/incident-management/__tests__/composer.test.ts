import { describe, expect, it } from "vitest";
import { composeAssignedResources } from "../services/resource-composer";
import type { Incident } from "@/features/dispatcher-workspace/types";
import type { Unit } from "@/features/dispatcher-workspace/types/resource";

function incident(dispatches: Incident["dispatches"]): Incident {
  return {
    id: "i1",
    number: "0001",
    category: "fire",
    source: "phone",
    status: "dispatched",
    priority: "high",
    title: null,
    description: null,
    address: null,
    latitude: null,
    longitude: null,
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
    dispatches,
  };
}

function unit(partial: Partial<Unit>): Unit {
  return {
    id: partial.id ?? "u1",
    code: partial.code ?? "АЦ-1",
    name: partial.name ?? "Автоцистерна 1",
    call_sign: partial.call_sign ?? "01",
    station_id: null,
    organization: partial.organization ?? { id: "o", code: "pch", name: "ПЧ-1" },
    vehicle_resource_id: partial.vehicle_resource_id ?? null,
    status: partial.status ?? {
      id: "s",
      code: "enroute",
      name: "Следует",
      is_operational: true,
      is_available_for_dispatch: false,
      color: "#1e88e5",
    },
    is_active: true,
    is_available: false,
    crew_count: partial.crew_count ?? 4,
    active_assignment_id: null,
    notes: null,
  };
}

describe("composeAssignedResources", () => {
  it("matches a dispatch to a unit by unit id", () => {
    const inc = incident([
      { id: "d1", resource_id: "u1", role: "primary", status: "en_route", assigned_at: "t", note: null },
    ]);
    const rows = composeAssignedResources(inc, [unit({ id: "u1" })]);
    expect(rows).toHaveLength(1);
    expect(rows[0].unitId).toBe("u1");
    expect(rows[0].code).toBe("АЦ-1");
    expect(rows[0].crewCount).toBe(4);
    expect(rows[0].unitStatus?.name).toBe("Следует");
    expect(rows[0].dispatchStatus).toBe("en_route");
  });

  it("matches by vehicle resource id", () => {
    const inc = incident([
      { id: "d1", resource_id: "veh-1", role: "primary", status: "assigned", assigned_at: "t", note: null },
    ]);
    const rows = composeAssignedResources(inc, [unit({ id: "u9", vehicle_resource_id: "veh-1" })]);
    expect(rows[0].unitId).toBe("u9");
  });

  it("keeps unmatched dispatches with a null unit id", () => {
    const inc = incident([
      { id: "d1", resource_id: "ghost", role: "primary", status: "assigned", assigned_at: "t", note: null },
    ]);
    const rows = composeAssignedResources(inc, [unit({ id: "u1" })]);
    expect(rows[0].unitId).toBeNull();
  });
});
