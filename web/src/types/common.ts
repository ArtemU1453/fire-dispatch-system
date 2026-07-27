import type { LucideIcon } from "lucide-react";

export type NotificationLevel = "info" | "success" | "warning" | "critical";

export interface AppNotification {
  id: string;
  level: NotificationLevel;
  title: string;
  message: string;
  createdAt: string;
  read: boolean;
}

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  permission?: string;
}
