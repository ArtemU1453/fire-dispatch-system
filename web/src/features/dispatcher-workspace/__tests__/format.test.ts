import { describe, expect, it } from "vitest";
import {
  categoryLabel,
  formatEta,
  isClosedStatus,
  priorityVariant,
  statusLabel,
} from "../utils/format";

describe("format helpers", () => {
  it("formats ETA compactly in Russian", () => {
    expect(formatEta(null)).toBe("—");
    expect(formatEta(420)).toBe("7 мин");
    expect(formatEta(3900)).toBe("1 ч 5 мин");
    expect(formatEta(3600)).toBe("1 ч");
  });

  it("maps priorities to badge variants", () => {
    expect(priorityVariant("critical")).toBe("danger");
    expect(priorityVariant("high")).toBe("warning");
    expect(priorityVariant("normal")).toBe("info");
    expect(priorityVariant("low")).toBe("outline");
  });

  it("localizes enum labels", () => {
    expect(statusLabel("on_scene")).toBe("На месте");
    expect(categoryLabel("road_accident")).toBe("ДТП");
  });

  it("detects terminal statuses", () => {
    expect(isClosedStatus("archived")).toBe(true);
    expect(isClosedStatus("confirmed")).toBe(false);
  });
});
