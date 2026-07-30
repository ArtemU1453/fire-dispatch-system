import { describe, expect, it } from "vitest";
import { __mapEventForTest as mapEvent } from "../services/realtime.service";
import type { DispatcherEvent } from "@/features/dispatcher-workspace/types";

const ID = "inc-1";

describe("IncidentRealtimeService event mapping", () => {
  it("maps a status change to IncidentUpdated (non-terminal)", () => {
    const e: DispatcherEvent = {
      type: "incident.status_changed",
      payload: { incident_id: ID, status: "on_scene" },
    };
    expect(mapEvent(ID, e)?.type).toBe("IncidentUpdated");
  });

  it("maps a terminal status change to IncidentClosed", () => {
    const e: DispatcherEvent = {
      type: "incident.status_changed",
      payload: { incident_id: ID, status: "completed" },
    };
    expect(mapEvent(ID, e)?.type).toBe("IncidentClosed");
  });

  it("ignores events for a different incident", () => {
    const e: DispatcherEvent = {
      type: "incident.updated",
      payload: { incident_id: "other" },
    };
    expect(mapEvent(ID, e)).toBeNull();
  });

  it("maps unit updates to ResourceStatusChanged", () => {
    const e: DispatcherEvent = { type: "unit.updated", payload: { unit_id: "u1" } };
    expect(mapEvent(ID, e)?.type).toBe("ResourceStatusChanged");
  });

  it("maps route updates for this incident to ETAChanged", () => {
    const e: DispatcherEvent = {
      type: "route.updated",
      payload: { incident_id: ID, unit_id: "u1" },
    };
    expect(mapEvent(ID, e)?.type).toBe("ETAChanged");
  });

  it("maps a log append to MessageReceived", () => {
    const e: DispatcherEvent = {
      type: "log.appended",
      payload: {
        id: "l1",
        occurred_at: "t",
        level: "info",
        category: "incident",
        action: "a",
        message: "m",
        incident_id: ID,
      },
    };
    expect(mapEvent(ID, e)?.type).toBe("MessageReceived");
  });
});
