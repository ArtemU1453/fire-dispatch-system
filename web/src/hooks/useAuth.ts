import { authApi } from "@/api/auth.api";
import { useAuthStore } from "@/store/auth.store";
import { useUserStore } from "@/store/user.store";
import type { LoginCredentials } from "@/types/auth";

/** Single entry point for authentication actions and identity. */
export function useAuth() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const setTokens = useAuthStore((s) => s.setTokens);
  const setRemember = useAuthStore((s) => s.setRemember);
  const clearTokens = useAuthStore((s) => s.clearTokens);
  const user = useUserStore((s) => s.user);
  const setUser = useUserStore((s) => s.setUser);
  const clearUser = useUserStore((s) => s.clearUser);
  const hasPermission = useUserStore((s) => s.hasPermission);
  const hasRole = useUserStore((s) => s.hasRole);

  async function login(creds: LoginCredentials) {
    const res = await authApi.login(creds);
    setRemember(!!creds.remember);
    setTokens(res.tokens);
    setUser(res.user);
    return res.user;
  }

  function logout() {
    clearTokens();
    clearUser();
  }

  return { isAuthenticated, user, login, logout, hasPermission, hasRole };
}
