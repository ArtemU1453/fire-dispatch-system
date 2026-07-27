import { useNavigate } from "react-router-dom";
import { Bell, LogOut, Settings, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useClock } from "@/hooks/useClock";
import { useAuth } from "@/hooks/useAuth";
import { formatDate, formatTime } from "@/lib/utils";
import { paths } from "@/routes/paths";
import { useNotificationStore } from "@/store/notification.store";

export function Header() {
  const now = useClock();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const togglePanel = useNotificationStore((s) => s.togglePanel);
  const unread = useNotificationStore((s) => s.items.filter((i) => !i.read).length);

  return (
    <header
      className="flex shrink-0 items-center justify-between gap-6 border-b border-border bg-panel px-5"
      style={{ height: "var(--header-height)" }}
    >
      <div className="flex items-center gap-3">
        <div className="grid h-9 w-9 place-items-center rounded-md bg-primary/15 text-primary">
          <ShieldAlert className="h-5 w-5" />
        </div>
        <div className="leading-tight">
          <div className="text-sm font-bold tracking-wide">
            AI Dispatcher <span className="text-primary">МЧС</span>
          </div>
          <div className="text-[11px] uppercase tracking-[2px] text-muted-foreground">
            Центр управления
          </div>
        </div>
      </div>

      <div className="hidden items-center gap-5 md:flex">
        <div className="text-right">
          <div className="font-mono text-xl font-bold tabular-nums">{formatTime(now)}</div>
        </div>
        <div className="h-8 w-px bg-border" />
        <div className="text-sm capitalize text-muted-foreground">{formatDate(now)}</div>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden text-right lg:block">
          <div className="text-sm font-semibold">{user?.fullName ?? "—"}</div>
          <div className="text-xs text-muted-foreground">{user?.roleLabel ?? "—"}</div>
        </div>
        <Button variant="ghost" size="icon" className="relative" onClick={togglePanel} aria-label="Уведомления">
          <Bell className="h-5 w-5" />
          {unread > 0 && (
            <span className="absolute -right-0.5 -top-0.5 grid h-5 min-w-5 place-items-center rounded-full bg-primary px-1 text-[11px] font-bold text-primary-foreground">
              {unread}
            </span>
          )}
        </Button>
        <Button variant="ghost" size="icon" onClick={() => navigate(paths.settings)} aria-label="Настройки">
          <Settings className="h-5 w-5" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => { logout(); navigate(paths.login); }}
          aria-label="Выход"
        >
          <LogOut className="h-5 w-5" />
        </Button>
      </div>
    </header>
  );
}
