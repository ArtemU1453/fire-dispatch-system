import {
  LayoutDashboard, Flame, Truck, Map, ScrollText, BarChart3, ShieldCheck, Settings,
} from "lucide-react";
import { paths } from "@/routes/paths";
import type { NavItem } from "@/types/common";

export const navItems: NavItem[] = [
  { to: paths.dashboard, label: "Рабочее место диспетчера", icon: LayoutDashboard },
  { to: paths.incidents, label: "Происшествия", icon: Flame },
  { to: paths.resources, label: "Подразделения", icon: Truck },
  { to: paths.map, label: "Карта", icon: Map },
  { to: paths.journal, label: "Журнал", icon: ScrollText },
  { to: paths.reports, label: "Аналитика", icon: BarChart3 },
  { to: paths.admin, label: "Администрирование", icon: ShieldCheck, permission: "admin.access" },
  { to: paths.settings, label: "Настройки", icon: Settings },
];
