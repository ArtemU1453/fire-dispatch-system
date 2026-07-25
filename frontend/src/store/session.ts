/**
 * Session store (client-side auth shell, RBAC-ready).
 *
 * The backend exposes no auth API at this stage, so the session lives on the
 * client. The shape (roles + a `can` permission check) is designed so a real
 * auth/RBAC backend can replace `login` without touching the UI. The session is
 * persisted to localStorage so a refresh keeps the dispatcher signed in.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type Role = 'dispatcher' | 'supervisor' | 'viewer';

export type Permission =
  | 'incident.create'
  | 'recommendation.request'
  | 'recommendation.confirm'
  | 'map.view';

const ROLE_PERMISSIONS: Record<Role, Permission[]> = {
  dispatcher: [
    'incident.create',
    'recommendation.request',
    'recommendation.confirm',
    'map.view',
  ],
  supervisor: [
    'incident.create',
    'recommendation.request',
    'recommendation.confirm',
    'map.view',
  ],
  viewer: ['map.view'],
};

export interface SessionUser {
  username: string;
  role: Role;
  shift: string;
}

interface SessionState {
  user: SessionUser | null;
  login: (user: SessionUser) => void;
  logout: () => void;
  can: (permission: Permission) => boolean;
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set, get) => ({
      user: null,
      login: (user) => set({ user }),
      logout: () => set({ user: null }),
      can: (permission) => {
        const role = get().user?.role;
        if (!role) return false;
        return ROLE_PERMISSIONS[role].includes(permission);
      },
    }),
    { name: 'dispatcher-session' },
  ),
);
