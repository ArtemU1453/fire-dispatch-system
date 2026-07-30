import { afterEach, describe, expect, it, vi } from "vitest";

const request = vi.fn();
vi.mock("@/api/client", () => ({ request: (...a: unknown[]) => request(...a) }));

import { ManagementService } from "../api/management.service";

afterEach(() => request.mockReset());

describe("ManagementService", () => {
  it("updateIncident issues a PUT with the patch", async () => {
    request.mockResolvedValueOnce({ id: "i1", number: "1", status: "confirmed" });
    await ManagementService.updateIncident("i1", { priority: "high" });
    const [cfg] = request.mock.calls[0];
    expect(cfg.method).toBe("PUT");
    expect(cfg.url).toBe("/incidents/i1");
    expect(cfg.data).toEqual({ priority: "high" });
  });

  it("changeUnitStatus PATCHes the unit with the status code", async () => {
    request.mockResolvedValueOnce({});
    await ManagementService.changeUnitStatus("u1", "on_scene", "i1", "Иванов");
    const [cfg] = request.mock.calls[0];
    expect(cfg.method).toBe("PATCH");
    expect(cfg.url).toBe("/units/u1/status");
    expect(cfg.data).toMatchObject({ status_code: "on_scene", incident_id: "i1" });
  });

  it("releaseUnit POSTs to the return endpoint", async () => {
    request.mockResolvedValueOnce({});
    await ManagementService.releaseUnit("u1", "Иванов");
    const [cfg] = request.mock.calls[0];
    expect(cfg.method).toBe("POST");
    expect(cfg.url).toBe("/units/u1/return");
    expect(cfg.params).toEqual({ actor_name: "Иванов" });
  });

  it("statusCatalog dedupes statuses by code", async () => {
    request.mockResolvedValueOnce([
      { status: { id: "1", code: "free", name: "Свободно", color: "#0f0", is_available_for_dispatch: true }, resource_count: 3 },
      { status: { id: "1", code: "free", name: "Свободно", color: "#0f0", is_available_for_dispatch: true }, resource_count: 1 },
      { status: { id: "2", code: "enroute", name: "Следует", color: "#00f", is_available_for_dispatch: false }, resource_count: 2 },
    ]);
    const out = await ManagementService.statusCatalog();
    expect(out).toHaveLength(2);
    expect(out.map((s) => s.code)).toEqual(["free", "enroute"]);
  });
});
