import { env } from "@/lib/env";
import { apiClient } from "./client";
import type { AuthResponse, AuthTokens, LoginCredentials } from "@/types/auth";
import type { Role, User } from "@/types/user";

const ROLE_LABELS: Record<Role, string> = {
  dispatcher: "Диспетчер",
  shift_lead: "Начальник смены",
  garrison_chief: "Руководитель гарнизона",
  fire_commander: "Руководитель тушения пожара",
  hq: "Оперативный штаб",
  admin: "Администратор",
};

interface RawUser {
  id: string;
  username: string;
  full_name?: string;
  fullName?: string;
  email?: string;
  role?: Role;
  permissions?: string[];
}

function mapUser(u: RawUser): User {
  const role: Role = u.role ?? "dispatcher";
  return {
    id: u.id,
    username: u.username,
    fullName: u.full_name ?? u.fullName ?? u.username,
    email: u.email,
    role,
    roleLabel: ROLE_LABELS[role] ?? role,
    permissions: u.permissions ?? [],
  };
}

function mapTokens(data: Record<string, unknown>): AuthTokens {
  return {
    accessToken: (data.access_token ?? data.accessToken) as string,
    refreshToken: (data.refresh_token ?? data.refreshToken) as string,
  };
}

export const authApi = {
  async login(creds: LoginCredentials): Promise<AuthResponse> {
    const { data } = await apiClient.post(env.authLoginPath, {
      username: creds.username,
      password: creds.password,
    });
    return { tokens: mapTokens(data), user: mapUser(data.user as RawUser) };
  },

  async me(): Promise<User> {
    const { data } = await apiClient.get<RawUser>(env.authMePath);
    return mapUser(data);
  },
};
