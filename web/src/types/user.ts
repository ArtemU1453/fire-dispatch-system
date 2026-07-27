export type Role =
  | "dispatcher"
  | "shift_lead"
  | "garrison_chief"
  | "fire_commander"
  | "hq"
  | "admin";

export interface User {
  id: string;
  username: string;
  fullName: string;
  email?: string;
  role: Role;
  roleLabel: string;
  permissions: string[];
}
