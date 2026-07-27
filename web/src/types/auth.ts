import type { User } from "./user";

export interface LoginCredentials {
  username: string;
  password: string;
  remember?: boolean;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

export interface AuthResponse {
  tokens: AuthTokens;
  user: User;
}
