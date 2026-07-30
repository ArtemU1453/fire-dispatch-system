import { describe, expect, it } from "vitest";
import {
  dispatchStatusLabel,
  dispatchStatusVariant,
  timelineCategory,
  filterTimeline,
  speedKmh,
} from "../utils";
import type { TimelineEntry } from "../types";

function entry(partial: Partial<TimelineEntry>): TimelineEntry {
  return {
    id: partial.id ?? crypto.randomUUID(),
    event_type: partial.event_type ?? "created",
    title: partial.title ?? "Событие",
    detail: partial.detail ?? null,
    actor_name: partial.actor_name ?? null,
    meta: null,
    occurred_at: partial.occurred_at ?? "2026-07-27T10:00:00Z",
  };
}

describe("management utils", () => {
  it("labels dispatch statuses", () => {
    expect(dispatchStatusLabel("en_route")).toBe("Выезд");
    expect(dispatchStatusLabel("on_scene")).toBe("На месте");
    expect(dispatchStatusVariant("on_scene")).toBe("success");
    expect(dispatchStatusVariant("cancelled")).toBe("outline");
  });

  it("classifies timeline categories", () => {
    expect(timelineCategory("created")).toBe("registration");
    expect(timelineCategory("units_assigned")).toBe("assignment");
    expect(timelineCategory("status_changed")).toBe("status");
    expect(timelineCategory("route_updated")).toBe("route");
    expect(timelineCategory("comment_added")).toBe("message");
  });

  it("filters the timeline by category and search", () => {
    const entries = [
      entry({ event_type: "created", title: "Регистрация" }),
      entry({ event_type: "units_assigned", title: "Назначение АЦ-1" }),
    ];
    expect(filterTimeline(entries, "", "assignment")).toHaveLength(1);
    expect(filterTimeline(entries, "АЦ-1", "all")).toHaveLength(1);
    expect(filterTimeline(entries, "нет", "all")).toHaveLength(0);
  });

  it("derives speed from two positions", () => {
    const prev = { latitude: 55.7, longitude: 37.6, recorded_at: "2026-07-27T10:00:00Z" };
    const next = { latitude: 55.71, longitude: 37.6, recorded_at: "2026-07-27T10:01:00Z" };
    const s = speedKmh(prev, next);
    expect(s).not.toBeNull();
    expect(s!).toBeGreaterThan(0);
    expect(speedKmh(null, next)).toBeNull();
  });
});
