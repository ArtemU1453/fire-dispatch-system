/**
 * Keyboard shortcuts for the registration workflow.
 *
 *  - F2          → open a new incident registration (global; see EnterpriseLayout)
 *  - Ctrl+Enter  → confirm the dispatch
 *  - Esc         → cancel / close
 */
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

/** Global F2 → navigate to the new-incident page. */
export function useNewIncidentHotkey() {
  const navigate = useNavigate();
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "F2" && !e.repeat) {
        e.preventDefault();
        navigate("/incidents/new");
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [navigate]);
}

interface RegistrationHotkeyHandlers {
  onConfirm: () => void;
  onCancel: () => void;
}

/** Ctrl/Cmd+Enter → confirm, Esc → cancel (scoped to the registration page). */
export function useRegistrationHotkeys({
  onConfirm,
  onCancel,
}: RegistrationHotkeyHandlers) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        onConfirm();
      } else if (e.key === "Escape") {
        e.preventDefault();
        onCancel();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onConfirm, onCancel]);
}
