import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";

const search = vi.fn();
const resolveArea = vi.fn();
vi.mock("../api", () => ({
  AddressService: {
    search: (...a: unknown[]) => search(...a),
    resolveArea: (...a: unknown[]) => resolveArea(...a),
  },
}));

import { AddressSearch } from "../components/AddressSearch";
import { useRegistrationStore } from "../store/registration.store";

function wrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

describe("AddressSearch", () => {
  beforeEach(() => {
    search.mockReset();
    resolveArea.mockReset();
    useRegistrationStore.getState().reset();
    search.mockResolvedValue([
      {
        id: "55.750000,37.610000:0",
        formatted_address: "ул. Ленина, 5",
        normalized_address: "ленина 5",
        latitude: 55.75,
        longitude: 37.61,
        accuracy: "rooftop",
        source: "nominatim",
      },
    ]);
    resolveArea.mockResolvedValue({
      region: "Москва",
      district: "Центральный",
      settlement: "Москва",
      street: "Ленина",
      house_number: "5",
      formatted_address: "ул. Ленина, 5",
    });
  });

  it("shows debounced suggestions after typing", async () => {
    render(<AddressSearch />, { wrapper: wrapper() });
    await userEvent.type(screen.getByLabelText(/Адрес происшествия/), "лен");
    expect(await screen.findByRole("option")).toHaveTextContent("ул. Ленина, 5");
  });

  it("resolves the chosen address into the store", async () => {
    render(<AddressSearch />, { wrapper: wrapper() });
    await userEvent.type(screen.getByLabelText(/Адрес происшествия/), "лен");
    const option = await screen.findByRole("option");
    await userEvent.click(option);

    await waitFor(() => {
      expect(useRegistrationStore.getState().location).not.toBeNull();
    });
    const loc = useRegistrationStore.getState().location;
    expect(loc?.address).toBe("ул. Ленина, 5");
    expect(loc?.area?.district).toBe("Центральный");
    // The resolved location panel shows the coordinates.
    expect(screen.getByText(/55\.75000, 37\.61000/)).toBeInTheDocument();
  });
});
