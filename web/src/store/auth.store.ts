import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AuthTokens } from "@/types/auth";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  remember: boolean;
  setTokens: (tokens: AuthTokens) => void;
  setRemember: (remember: boolean) => void;
  clearTokens: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      remember: true,
      setTokens: (t) =>
        set({ accessToken: t.accessToken, refreshToken: t.refreshToken, isAuthenticated: true }),
      setRemember: (remember) => set({ remember }),
      clearTokens: () =>
        set({ accessToken: null, refreshToken: null, isAuthenticated: false }),
    }),
    { name: "aid.auth" },
  ),
);
