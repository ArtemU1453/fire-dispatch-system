import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { AxiosRequestConfig } from "axios";
import type { ReactNode } from "react";

const ID = "inc-1";

const incidentBody = {
  id: ID,
  number: "2026-000777",
  category: "fire",
  source: "phone",
  status: "dispatched",
  priority: "high",
  title: "Пожар",
  description: null,
  address: "ул. Ленина, 5",
  latitude: 55.75,
  longitude: 37.61,
  danger_level: null,
  object_type: null,
  reporter_name: "Иванов",
  reporter_contact: "+79000000000",
  reported_at: "2026-07-27T10:00:00Z",
  confirmed_at: null,
  closed_at: null,
  allowed_transitions: ["localized", "completed"],
  locations: [],
  comments: [],
  timeline: [],
  dispatches: [
    { id: "d1", resource_id: "u1", role: "primary", status: "en_route", assigned_at: "2026-07-27T10:01:00Z", note: null },
  ],
};

const units = [
  {
    id: "u1", code: "АЦ-1", name: "Автоцистерна 1", call_sign: "01", station_id: null,
    organization: { id: "o", code: "pch", name: "ПЧ-1" }, vehicle_resource_id: null,
    status: { id: "s1", code: "enroute", name: "Следует", is_operational: true, is_available_for_dispatch: false, color: "#00f" },
    is_active: true, is_available: false, crew_count: 4, active_assignment_id: "a1", notes: null,
  },
  {
    id: "u2", code: "АЦ-2", name: "Автоцистерна 2", call_sign: "02", station_id: null,
    organization: { id: "o", code: "pch", name: "ПЧ-1" }, vehicle_resource_id: null,
    status: { id: "s2", code: "free", name: "Свободно", is_operational: true, is_available_for_dispatch: true, color: "#0f0" },
    is_active: true, is_available: true, crew_count: 4, active_assignment_id: null, notes: null,
  },
];

const request = vi.fn((config: AxiosRequestConfig) => {
  const url = config.url ?? "";
  const method = (config.method ?? "get").toLowerCase();
  if (url === `/incidents/${ID}` && method === "get") return Promise.resolve(incidentBody);
  if (url === `/incidents/${ID}/timeline`) return Promise.resolve({ incident_id: ID, count: 0, entries: [] });
  if (url === "/units") return Promise.resolve(units);
  if (url === "/resources/status")
    return Promise.resolve([
      { status: { id: "s1", code: "enroute", name: "Следует", color: "#00f", is_available_for_dispatch: false }, resource_count: 1 },
      { status: { id: "s2", code: "free", name: "Свободно", color: "#0f0", is_available_for_dispatch: true }, resource_count: 5 },
    ]);
  if (url === `/units/u1/location`) return Promise.resolve({ resource_id: "u1", latitude: 55.74, longitude: 37.6, recorded_at: null, source: "stored" });
  if (url === "/routing/eta") return Promise.resolve({ eta_seconds: 240, eta_minutes: 4, distance_meters: 900, is_fallback: false });
  if (url.includes("/units") && method === "post") return Promise.resolve({});
  if (url.includes("/return") && method === "post") return Promise.resolve({});
  if (url.includes("/status") && method === "patch") return Promise.resolve({ id: ID, status: "localized", allowed_transitions: [], changed_at: "t" });
  return Promise.resolve({});
});

vi.mock("@/api/client", () => ({ request: (c: AxiosRequestConfig) => request(c) }));
vi.mock("../components/IncidentMap", () => ({ IncidentMap: () => <div data-testid="map" /> }));

import { IncidentManagement } from "../components/IncidentManagement";
import { useManagementStore } from "../store/management.store";

function renderScreen() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[`/incidents/${ID}`]}>{children}</MemoryRouter>
    </QueryClientProvider>
  );
  return render(<IncidentManagement incidentId={ID} />, { wrapper });
}

describe("incident management (integration)", () => {
  beforeEach(() => {
    request.mockClear();
    useManagementStore.getState().reset();
  });

  it("shows the assigned unit and the incident card", async () => {
    renderScreen();
    expect(await screen.findAllByText(/АЦ-1/)).not.toHaveLength(0);
    expect(screen.getAllByText(/2026-000777/).length).toBeGreaterThan(0);
  });

  it("cancels a dispatch via the release action", async () => {
    renderScreen();
    await screen.findAllByText(/АЦ-1/);
    await userEvent.click(screen.getByRole("button", { name: "Отменить высылку" }));
    await waitFor(() => {
      const released = request.mock.calls.some(
        ([c]) => c.url === "/units/u1/return" && (c.method ?? "").toLowerCase() === "post",
      );
      expect(released).toBe(true);
    });
  });

  it("adds a resource through the ResourceManager", async () => {
    renderScreen();
    await screen.findAllByText(/АЦ-1/);
    await userEvent.click(screen.getByRole("button", { name: /Добавить/ }));
    const dialog = await screen.findByRole("dialog");
    await userEvent.click(within(dialog).getByText(/АЦ-2/));
    await userEvent.click(within(dialog).getByRole("button", { name: /Назначить/ }));
    await waitFor(() => {
      const assigned = request.mock.calls.some(
        ([c]) => c.url === `/incidents/${ID}/units` && (c.method ?? "").toLowerCase() === "post",
      );
      expect(assigned).toBe(true);
    });
  });

  it("opens the close modal and applies a status change", async () => {
    renderScreen();
    await screen.findAllByText(/АЦ-1/);
    await userEvent.click(screen.getByRole("button", { name: /Закрыть/ }));
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText(/Закрыть \/ изменить статус/)).toBeInTheDocument();
  });
});
