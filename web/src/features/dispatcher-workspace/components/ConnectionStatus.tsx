/**
 * Live WebSocket connection indicator for the workspace header.
 */
import { memo } from "react";
import { Wifi, WifiOff, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { SocketStatus } from "../types";

const LABELS: Record<SocketStatus, string> = {
  connecting: "Подключение…",
  open: "В сети",
  closed: "Отключено",
  reconnecting: "Переподключение…",
  disabled: "Недоступно",
};

interface Props {
  status: SocketStatus;
  className?: string;
}

function ConnectionStatusBase({ status, className }: Props) {
  const online = status === "open";
  const pending = status === "connecting" || status === "reconnecting";
  const color = online
    ? "text-success"
    : pending
      ? "text-warning"
      : "text-muted-foreground";

  return (
    <div
      className={cn("flex items-center gap-1.5 text-xs font-medium", color, className)}
      role="status"
      aria-live="polite"
      title={`Канал реального времени: ${LABELS[status]}`}
    >
      {online ? (
        <Wifi className="h-3.5 w-3.5" aria-hidden />
      ) : pending ? (
        <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
      ) : (
        <WifiOff className="h-3.5 w-3.5" aria-hidden />
      )}
      <span>{LABELS[status]}</span>
    </div>
  );
}

export const ConnectionStatus = memo(ConnectionStatusBase);
