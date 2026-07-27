import { describe, expect, it } from "vitest";
import { filterAndSortIncidents } from "../utils/filter";
import type { IncidentFilters } from "../store/dispatcher.store";
import type { IncidentSummary } from "../types";

function inc(partial: Partial<IncidentSummary>): IncidentSummary {
  return {
    id: partial.id ?? crypto.randomUUID(),
    number: partial.number ?? "0001",
    category: partial.category ?? "fire",
    status: partial.status ?? "confirmed",
    priority: partial.priority ?? "normal",
    title: partial.title ?? null,
    address: partial.address ?? null,
    reported_at: partial.reported_at ?? "2026-07-27T10:00:00Z",
  };
}

const base: IncidentFilters = {
  search: "",
  statuses: [],
  priorities: [],
  categories: [],
  sort: "reported_desc",
};

describe("filterAndSortIncidents", () => {
  const items = [
    inc({ number: "0001", priority: "low", reported_at: "2026-07-27T08:00:00Z" }),
    inc({ number: "0002", priority: "critical", reported_at: "2026-07-27T09:00:00Z", address: "ул. Ленина, 5" }),
    inc({ number: "0003", priority: "high", reported_at: "2026-07-27T10:00:00Z" }),
  ];

  it("sorts newest first by default", () => {
    const out = filterAndSortIncidents(items, base);
    expect(out.map((i) => i.number)).toEqual(["0003", "0002", "0001"]);
  });

  it("sorts by priority rank", () => {
    const out = filterAndSortIncidents(items, { ...base, sort: "priority" });
    expect(out[0].priority).toBe("critical");
    expect(out[out.length - 1].priority).toBe("low");
  });

  it("filters by priority", () => {
    const out = filterAndSortIncidents(items, { ...base, priorities: ["critical"] });
    expect(out).toHaveLength(1);
    expect(out[0].number).toBe("0002");
  });

  it("matches search against number and address", () => {
    expect(filterAndSortIncidents(items, { ...base, search: "Ленина" })).toHaveLength(1);
    expect(filterAndSortIncidents(items, { ...base, search: "0003" })).toHaveLength(1);
    expect(filterAndSortIncidents(items, { ...base, search: "нет-такого" })).toHaveLength(0);
  });
});
