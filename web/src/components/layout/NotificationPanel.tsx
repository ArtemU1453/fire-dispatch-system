import { CheckCheck, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useNotificationStore } from "@/store/notification.store";
import type { NotificationLevel } from "@/types/common";

const levelBar: Record<NotificationLevel, string> = {
  critical: "border-l-danger",
  warning: "border-l-warning",
  success: "border-l-success",
  info: "border-l-info",
};

export function NotificationPanel() {
  const open = useNotificationStore((s) => s.panelOpen);
  const setOpen = useNotificationStore((s) => s.setPanelOpen);
  const items = useNotificationStore((s) => s.items);
  const markAllRead = useNotificationStore((s) => s.markAllRead);
  const markRead = useNotificationStore((s) => s.markRead);

  return (
    <>
      {open && <div className="fixed inset-0 z-40 bg-black/40" onClick={() => setOpen(false)} />}
      <div
        className={cn(
          "fixed right-0 top-0 z-50 flex h-full flex-col border-l border-border bg-panel shadow-2xl transition-transform duration-200",
          open ? "translate-x-0" : "translate-x-full",
        )}
        style={{ width: "var(--notification-width)" }}
        aria-hidden={!open}
      >
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Уведомления</div>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="icon" onClick={markAllRead} aria-label="Прочитать все">
              <CheckCheck className="h-5 w-5" />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => setOpen(false)} aria-label="Закрыть">
              <X className="h-5 w-5" />
            </Button>
          </div>
        </div>
        <div className="flex-1 space-y-2 overflow-auto p-4">
          {items.length === 0 && <p className="p-6 text-center text-sm text-muted-foreground">Нет уведомлений</p>}
          {items.map((n) => (
            <button
              key={n.id}
              onClick={() => markRead(n.id)}
              className={cn(
                "block w-full rounded-md border border-border border-l-4 bg-card p-3 text-left transition hover:bg-secondary/40",
                levelBar[n.level],
                !n.read && "ring-1 ring-inset ring-accent/30",
              )}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold">{n.title}</span>
                {!n.read && <span className="h-2 w-2 rounded-full bg-accent" />}
              </div>
              <p className="mt-1 text-sm text-muted-foreground">{n.message}</p>
            </button>
          ))}
        </div>
      </div>
    </>
  );
}
