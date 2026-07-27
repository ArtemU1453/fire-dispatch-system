import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Role, User } from "@/types/user";

interface UserState {
  user: User | null;
  setUser: (user: User | null) => void;
  clearUser: () => void;
  hasPermission: (code: string) => boolean;
  hasRole: (...roles: Role[]) => boolean;
}

export const useUserStore = create<UserState>()(
  persist(
    (set, get) => ({
      user: null,
      setUser: (user) => set({ user }),
      clearUser: () => set({ user: null }),
      hasPermission: (code) => {
        const u = get().user;
        if (!u) return false;
        return u.role === "admin" || u.permissions.includes(code);
      },
      hasRole: (...roles) => {
        const u = get().user;
        return !!u && roles.includes(u.role);
      },
    }),
    { name: "aid.user" },
  ),
);
