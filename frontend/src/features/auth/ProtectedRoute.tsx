import type { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';

import { useSessionStore } from '../../store/session';

/** Gates the workstation behind a session (RBAC-ready). */
export function ProtectedRoute({ children }: { children: ReactNode }) {
  const user = useSessionStore((s) => s.user);
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
