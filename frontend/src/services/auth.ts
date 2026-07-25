/**
 * Auth service (client-side shell).
 *
 * The backend has no auth API at this stage, so this validates the form locally
 * and produces a session. It is the single seam where a real auth/RBAC call will
 * be introduced later — the UI depends only on `authenticate`.
 */
import type { Role, SessionUser } from '../store/session';

export interface Credentials {
  username: string;
  password: string;
  shift: string;
  role: Role;
}

export async function authenticate(credentials: Credentials): Promise<SessionUser> {
  const username = credentials.username.trim();
  if (!username || !credentials.password) {
    throw new Error('Введите имя пользователя и пароль.');
  }
  // Placeholder: accept any non-empty credentials. Replace with a real backend
  // authentication call when RBAC lands.
  return {
    username,
    role: credentials.role,
    shift: credentials.shift || 'Дежурная смена',
  };
}
