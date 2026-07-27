import { NavLink } from "react-router-dom";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { cn } from "@/lib/utils";
import { navItems } from "./nav";
import { useSettingsStore } from "@/store/settings.store";

export function Sidebar() {
  const collapsed = useSettingsStore((s) => s.sidebarCollapsed);
  const toggle = useSettingsStore((s) => s.toggleSidebar);
  const width = collapsed ? "var(--sidebar-width-collapsed)" : "var(--sidebar-width)";

  return (
    <aside
      className="flex shrink-0 flex-col border-r border-border bg-panel transition-[width] duration-200"
      style={{ width }}
    >
      <nav className="flex flex-1 flex-col gap-1 p-3">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            title={label}
            className={({ isActive }) =>
              cn(
                "group flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-secondary text-foreground shadow-[inset_2px_0_0_hsl(var(--primary))]"
                  : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground",
              )
            }
          >
            <Icon className="h-5 w-5 shrink-0" />
            {!collapsed && <span className="truncate">{label}</span>}
          </NavLink>
        ))}
      </nav>
      <button
        onClick={toggle}
        className="flex items-center gap-3 border-t border-border px-4 py-3 text-sm text-muted-foreground hover:text-foreground"
      >
        {collapsed ? <PanelLeftOpen className="h-5 w-5" /> : <><PanelLeftClose className="h-5 w-5" /> Свернуть</>}
      </button>
    </aside>
  );
}
