import { beforeEach, describe, expect, it } from "vitest";
import { useDispatcherStore } from "../store/dispatcher.store";

function reset() {
  useDispatcherStore.setState({
    selectedIncidentId: null,
    selectedUnitId: null,
    flyToIncidentId: null,
  });
  useDispatcherStore.getState().resetFilters();
}

describe("DispatcherStore", () => {
  beforeEach(reset);

  it("selects an incident and clears the unit selection", () => {
    const s = useDispatcherStore.getState();
    s.selectUnit("u1");
    s.selectIncident("i1");
    const next = useDispatcherStore.getState();
    expect(next.selectedIncidentId).toBe("i1");
    expect(next.selectedUnitId).toBeNull();
  });

  it("toggles map layers", () => {
    const before = useDispatcherStore.getState().map.layers.hydrants;
    useDispatcherStore.getState().toggleLayer("hydrants");
    expect(useDispatcherStore.getState().map.layers.hydrants).toBe(!before);
  });

  it("merges filter patches", () => {
    useDispatcherStore.getState().setFilters({ search: "пожар", sort: "priority" });
    const f = useDispatcherStore.getState().filters;
    expect(f.search).toBe("пожар");
    expect(f.sort).toBe("priority");
  });

  it("requestFlyTo also selects the incident", () => {
    useDispatcherStore.getState().requestFlyTo("i9");
    const s = useDispatcherStore.getState();
    expect(s.flyToIncidentId).toBe("i9");
    expect(s.selectedIncidentId).toBe("i9");
    s.clearFlyTo();
    expect(useDispatcherStore.getState().flyToIncidentId).toBeNull();
  });
});
