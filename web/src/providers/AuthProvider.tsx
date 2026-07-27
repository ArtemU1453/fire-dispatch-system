import { type ReactNode, useEffect } from "react";
import { env } from "@/lib/env";
import { useAuthStore } from "@/store/auth.store";
import { useUserStore } from "@/store/user.store";

/**
 * Cross-cutting auth concerns: idle auto-logout after inactivity. Token refresh
 * and 401 handling live in the Axios client; protected routing lives in the
 * router. Keeping them separate honours SRP.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    let timer: number;
    const reset = () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        if (useAuthStore.getState().isAuthenticated) {
          useAuthStore.getState().clearTokens();
          useUserStore.getState().clearUser();
        }
      }, env.idleTimeout);
    };
    const events = ["mousemove", "keydown", "click", "scroll"];
    events.forEach((e) => window.addEventListener(e, reset, { passive: true }));
    reset();
    return () => {
      window.clearTimeout(timer);
      events.forEach((e) => window.removeEventListener(e, reset));
    };
  }, []);

  return <>{children}</>;
}
