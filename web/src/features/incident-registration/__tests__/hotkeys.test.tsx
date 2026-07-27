import { describe, expect, it, vi } from "vitest";
import { renderHook } from "@testing-library/react";
import { act } from "react";

const navigate = vi.fn();
vi.mock("react-router-dom", () => ({ useNavigate: () => navigate }));

import { useNewIncidentHotkey, useRegistrationHotkeys } from "../hooks/useHotkeys";

function press(key: string, opts: KeyboardEventInit = {}) {
  act(() => {
    window.dispatchEvent(new KeyboardEvent("keydown", { key, ...opts }));
  });
}

describe("registration hotkeys", () => {
  it("F2 navigates to the new-incident page", () => {
    navigate.mockReset();
    renderHook(() => useNewIncidentHotkey());
    press("F2");
    expect(navigate).toHaveBeenCalledWith("/incidents/new");
  });

  it("Ctrl+Enter confirms and Esc cancels", () => {
    const onConfirm = vi.fn();
    const onCancel = vi.fn();
    renderHook(() => useRegistrationHotkeys({ onConfirm, onCancel }));
    press("Enter", { ctrlKey: true });
    expect(onConfirm).toHaveBeenCalledTimes(1);
    press("Escape");
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});
