import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { act } from "react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { AxiosRequestConfig } from "axios";
import type { ReactNode } from "react";

const TYPE_ID = "11111111-1111-1111-1111-111111111111";

// Route every API call at the shared client boundary — this exercises the real
// service, hook, store and component code for the whole workflow.
const request = vi.fn((config: AxiosRequestConfig) => {
  const url = config.url ?? "";
  const method = (config.method ?? "get").toLowerCase();
  if (url === "/admin/directories/incident_types")
    return Promise.resolve([{ id: TYPE_ID, code: "fire", name: "Пожар", is_deleted: false }]);
  if (url === "/geocode")
    return Promise.resolve({
      query: "лен",
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
  if (url === "/reverse")
    return Promise.resolve({
      success: true,
      error: null,
      address: { region: "Москва", district: "Центральный", settlement: "Москва", street: "Ленина", house_number: "5", formatted_address: "ул. Ленина, 5" },
    });
  if (url === "/resources/nearest")
    return Promise.resolve({
      total: 1,
      count: 1,
      items: [
        {
          id: "u1",
          code: "АЦ-1",
          name: "Автоцистерна 1",
          latitude: 55.74,
          longitude: 37.6,
          distance_meters: 1200,
          resource_type: { id: "t", code: "ac", name: "Автоцистерна" },
          availability_status: { id: "s", code: "free", name: "Свободен" },
        },
      ],
    });
  if (url === "/dispatch/preview")
    return Promise.resolve({
      recommendation: {
        status: "recommended",
        sufficient: true,
        confidence: "high",
        confidence_score: 0.9,
        total_candidates: 2,
        primary_units: [
          {
            id: "rec1",
            resource_id: "u1",
            code: "АЦ-1",
            name: "Автоцистерна 1",
            role: "primary",
            distance_meters: 1200,
            score: 0.9,
            readiness: "ready",
            capabilities: ["water"],
            reasons: ["ближайшее подразделение"],
            resource_type: null,
            organization: null,
          },
        ],
        reserve_units: [],
        summary: { missing_capabilities: [], messages: [] },
        messages: [],
        reasons: [],
      },
    });
  if (url === "/routing/eta")
    return Promise.resolve({ eta_seconds: 300, eta_minutes: 5, distance_meters: 1200, is_fallback: false });
  if (url === "/incidents" && method === "post")
    return Promise.resolve({ id: "inc-1", number: "2026-000123", status: "created" });
  if (url.includes("/units") && method === "post") return Promise.resolve({});
  return Promise.resolve({});
});

vi.mock("@/api/client", () => ({ request: (c: AxiosRequestConfig) => request(c) }));
// The OpenLayers map cannot render in jsdom; the flow doesn't depend on it.
vi.mock("../components/RegistrationMap", () => ({ RegistrationMap: () => <div data-testid="map" /> }));

import { IncidentRegistration } from "../components/IncidentRegistration";
import { useRegistrationStore } from "../store/registration.store";

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={["/incidents/new"]}>{children}</MemoryRouter>
    </QueryClientProvider>
  );
  return render(<IncidentRegistration />, { wrapper });
}

describe("incident registration workflow (integration)", () => {
  beforeEach(() => {
    request.mockClear();
    useRegistrationStore.getState().reset();
  });

  it("runs the full flow: address → recommendation → confirm → dispatch", async () => {
    renderPage();

    // Step 2 — search & pick an address (resolves location).
    await userEvent.type(screen.getByLabelText(/Адрес происшествия/), "лен");
    await userEvent.click(await screen.findByRole("option"));
    await waitFor(() =>
      expect(useRegistrationStore.getState().location).not.toBeNull(),
    );

    // Choose the incident type (drives the Dispatch Engine preview).
    act(() => {
      useRegistrationStore.setState((s) => ({
        form: { ...s.form, incidentTypeId: TYPE_ID },
      }));
    });

    // Step 4 — the recommendation appears and preselects the primary unit.
    expect(await screen.findAllByText(/Автоцистерна 1/)).not.toHaveLength(0);
    await waitFor(() =>
      expect(useRegistrationStore.getState().selectedUnits).toHaveLength(1),
    );

    // Step 6 — open the confirmation modal and confirm.
    await userEvent.click(
      screen.getByRole("button", { name: /Передать в Dispatch Engine/ }),
    );
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText(/Подтвердить высылку/)).toBeInTheDocument();
    await userEvent.click(
      within(dialog).getByRole("button", { name: /Передать в Dispatch Engine/ }),
    );

    // Step 7 — the incident was created and units assigned (Dispatch Engine).
    await waitFor(() => {
      const posted = request.mock.calls.some(
        ([c]) => c.url === "/incidents" && (c.method ?? "").toLowerCase() === "post",
      );
      expect(posted).toBe(true);
    });
    await waitFor(() =>
      expect(useRegistrationStore.getState().createdIncidentNumber).toBe("2026-000123"),
    );
  });
});
