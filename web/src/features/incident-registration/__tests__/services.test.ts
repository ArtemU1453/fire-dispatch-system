import { afterEach, describe, expect, it, vi } from "vitest";

const request = vi.fn();
vi.mock("@/api/client", () => ({ request: (...args: unknown[]) => request(...args) }));

import { AddressService } from "../api/address.service";
import { NearestService } from "../api/nearest.service";
import { DispatchService } from "../api/dispatch.service";
import { CatalogService } from "../api/catalog.service";

afterEach(() => request.mockReset());

describe("AddressService", () => {
  it("maps geocode results into candidates with stable ids", async () => {
    request.mockResolvedValueOnce({
      query: "ленина",
      success: true,
      error: null,
      count: 1,
      results: [
        {
          formatted_address: "ул. Ленина, 5",
          normalized_address: "ленина 5",
          latitude: 55.75,
          longitude: 37.61,
          accuracy: "rooftop",
          source: "nominatim",
        },
      ],
    });
    const out = await AddressService.search("ленина");
    expect(out).toHaveLength(1);
    expect(out[0].formatted_address).toBe("ул. Ленина, 5");
    expect(out[0].id).toContain("55.75");
  });

  it("returns null area when reverse geocode has no address", async () => {
    request.mockResolvedValueOnce({ success: true, error: null, address: null });
    expect(await AddressService.resolveArea(55.75, 37.61)).toBeNull();
  });
});

describe("NearestService", () => {
  it("flattens ref labels", async () => {
    request.mockResolvedValueOnce({
      total: 1,
      count: 1,
      items: [
        {
          id: "u1",
          code: "АЦ-1",
          name: "Автоцистерна 1",
          latitude: 55.7,
          longitude: 37.6,
          distance_meters: 800,
          resource_type: { id: "t", code: "ac", name: "Автоцистерна" },
          availability_status: { id: "s", code: "free", name: "Свободен" },
        },
      ],
    });
    const out = await NearestService.near(55.7, 37.6);
    expect(out[0].resource_type).toBe("Автоцистерна");
    expect(out[0].availability_status).toBe("Свободен");
  });
});

describe("DispatchService", () => {
  it("maps the recommendation envelope", async () => {
    request.mockResolvedValueOnce({
      recommendation: {
        status: "recommended",
        sufficient: true,
        confidence: "high",
        confidence_score: 0.9,
        total_candidates: 3,
        primary_units: [
          {
            id: "r1",
            resource_id: "u1",
            code: "АЦ-1",
            name: "Автоцистерна 1",
            role: "primary",
            distance_meters: 1000,
            score: 0.9,
            readiness: "ready",
            capabilities: ["water"],
            reasons: ["ближайшее"],
            resource_type: null,
            organization: { id: "o", code: "pch1", name: "ПЧ-1" },
          },
        ],
        reserve_units: [],
        summary: { missing_capabilities: ["ladder"], messages: [] },
        messages: [],
        reasons: ["по регламенту"],
      },
    });
    const rec = await DispatchService.preview({
      incidentTypeId: "t1",
      latitude: 55.7,
      longitude: 37.6,
    });
    expect(rec.confidence).toBe("high");
    expect(rec.primary_units[0].organization).toBe("ПЧ-1");
    expect(rec.missing_capabilities).toEqual(["ladder"]);
  });
});

describe("CatalogService", () => {
  it("filters out deleted directory items", async () => {
    request.mockResolvedValueOnce([
      { id: "1", code: "fire", name: "Пожар", is_deleted: false },
      { id: "2", code: "old", name: "Устаревший", is_deleted: true },
    ]);
    const out = await CatalogService.incidentTypes();
    expect(out).toHaveLength(1);
    expect(out[0].name).toBe("Пожар");
  });
});
