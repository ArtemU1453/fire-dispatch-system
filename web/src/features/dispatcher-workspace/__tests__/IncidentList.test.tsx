import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import type { IncidentSummary } from "../types";

// Mock the feature API so the list renders real component logic over stub data
// (the transport layer is exercised separately; here we test rendering, data
// wiring, filtering and selection).
const listActive = vi.fn();
vi.mock("../api", () => ({
  IncidentService: {
    listActive: (...args: unknown[]) => listActive(...args),
  },
}));

import { IncidentList } from "../components/IncidentList";
import { useDispatcherStore } from "../store/dispatcher.store";

const SAMPLE: IncidentSummary[] = [
  {
    id: "i1",
    number: "0001",
    category: "fire",
    status: "confirmed",
    priority: "critical",
    title: "Пожар в здании",
    address: "ул. Ленина, 5",
    reported_at: "2026-07-27T09:00:00Z",
  },
  {
    id: "i2",
    number: "0002",
    category: "road_accident",
    status: "dispatched",
    priority: "normal",
    title: "ДТП на перекрёстке",
    address: "пр. Мира, 12",
    reported_at: "2026-07-27T10:00:00Z",
  },
];

function wrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

describe("IncidentList", () => {
  beforeEach(() => {
    listActive.mockReset();
    listActive.mockResolvedValue(SAMPLE);
    useDispatcherStore.setState({ selectedIncidentId: null });
    useDispatcherStore.getState().resetFilters();
  });

  it("renders active incidents fetched from the API", async () => {
    render(<IncidentList />, { wrapper: wrapper() });
    expect(await screen.findByText("№ 0001")).toBeInTheDocument();
    expect(screen.getByText("№ 0002")).toBeInTheDocument();
  });

  it("filters the list by search text", async () => {
    render(<IncidentList />, { wrapper: wrapper() });
    await screen.findByText("№ 0001");

    const search = screen.getByLabelText("Поиск происшествий");
    await userEvent.type(search, "ДТП");

    await waitFor(() => {
      expect(screen.queryByText("№ 0001")).not.toBeInTheDocument();
    });
    expect(screen.getByText("№ 0002")).toBeInTheDocument();
  });

  it("selects an incident on click", async () => {
    render(<IncidentList />, { wrapper: wrapper() });
    const option = (await screen.findByText("№ 0001")).closest('[role="option"]');
    expect(option).not.toBeNull();
    await userEvent.click(within(option as HTMLElement).getByText("№ 0001"));
    expect(useDispatcherStore.getState().selectedIncidentId).toBe("i1");
  });
});
