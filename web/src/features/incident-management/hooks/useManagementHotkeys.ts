/**
 * Management screen hotkeys:
 *   Ctrl+R        → add resource
 *   Ctrl+Shift+R  → replace resource
 *   Ctrl+L        → close incident
 *   Ctrl+P        → print card
 * Browser defaults (reload / print) are suppressed while the screen is open.
 */
import { useEffect } from "react";

interface Handlers {
  onAddResource: () => void;
  onReplace: () => void;
  onClose: () => void;
  onPrint: () => void;
}

export function useManagementHotkeys({
  onAddResource,
  onReplace,
  onClose,
  onPrint,
}: Handlers) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const mod = e.ctrlKey || e.metaKey;
      if (!mod) return;
      const key = e.key.toLowerCase();
      if (key === "r" && e.shiftKey) {
        e.preventDefault();
        onReplace();
      } else if (key === "r") {
        e.preventDefault();
        onAddResource();
      } else if (key === "l") {
        e.preventDefault();
        onClose();
      } else if (key === "p") {
        e.preventDefault();
        onPrint();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onAddResource, onReplace, onClose, onPrint]);
}
