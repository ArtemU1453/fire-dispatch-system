import { type ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuthStore } from "@/store/auth.store";
import { useUserStore } from "@/store/user.store";
import { paths } from "./paths";

/** Guards a subtree: redirects unauthenticated users to /login (RBAC-ready). */
export function ProtectedRoute({
  children,
  permission,
}: {
  children: ReactNode;
  permission?: string;
}) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const hasPermission = useUserStore((s) => s.hasPermission);
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to={paths.login} replace state={{ from: location.pathname }} />;
  }
  if (permission && !hasPermission(permission)) {
    return <Navigate to={paths.dashboard} replace />;
  }
  return <>{children}</>;
}
