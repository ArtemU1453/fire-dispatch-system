import { beforeEach, describe, expect, it } from "vitest";
import { useManagementStore } from "../store/management.store";

describe("IncidentManagementStore", () => {
  beforeEach(() => useManagementStore.getState().reset());

  it("selects a resource", () => {
    useManagementStore.getState().selectResource("r1");
    expect(useManagementStore.getState().selectedResourceId).toBe("r1");
  });

  it("toggles a map layer", () => {
    const before = useManagementStore.getState().map.layers.hydrants;
    useManagementStore.getState().toggleLayer("hydrants");
    expect(useManagementStore.getState().map.layers.hydrants).toBe(!before);
  });

  it("merges timeline filters", () => {
    useManagementStore.getState().setTimelineFilters({ search: "выезд", category: "status" });
    const t = useManagementStore.getState().timeline;
    expect(t.search).toBe("выезд");
    expect(t.category).toBe("status");
  });

  it("reset clears selection and timeline filters", () => {
    useManagementStore.getState().selectResource("r1");
    useManagementStore.getState().setTimelineFilters({ search: "x" });
    useManagementStore.getState().reset();
    const s = useManagementStore.getState();
    expect(s.selectedResourceId).toBeNull();
    expect(s.timeline.search).toBe("");
  });
});
