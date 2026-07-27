/**
 * HeaderStats — the operational KPI strip shown at the top of the workspace:
 * active incidents, free units, busy units, average ETA. All figures are live
 * (StatisticsService aggregates real API data).
 */
import { memo } from "react";
import { Activity, Truck, Clock, ShieldAlert } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { useWorkspaceStats } from "../hooks";
import { formatEta } from "../utils/format";

interface StatProps {
  icon: LucideIcon;
  label: string;
  value: string;
  tone: string;
}

const StatItem = memo(function StatItem({ icon: Icon, label, value, tone }: StatProps) {
  return (
    <div className="flex items-center gap-2.5 rounded-md border border-border bg-panel px-3 py-1.5">
      <Icon className={cn("h-4 w-4 shrink-0", tone)} aria-hidden />
      <div className="flex flex-col leading-tight">
        <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
          {label}
        </span>
        <span className="text-sm font-semibold tabular-nums">{value}</span>
      </div>
    </div>
  );
});

function HeaderStatsBase({ className }: { className?: string }) {
  const { data, isLoading, isError } = useWorkspaceStats();

  if (isLoading) {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-32 rounded-md" />
        ))}
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className={cn("text-xs text-muted-foreground", className)} role="status">
        Статистика недоступна
      </div>
    );
  }

  return (
    <div className={cn("flex items-center gap-2", className)} aria-label="Оперативная статистика">
      <StatItem
        icon={ShieldAlert}
        label="Активные"
        value={String(data.activeIncidents)}
        tone="text-danger"
      />
      <StatItem
        icon={Truck}
        label="Свободно"
        value={String(data.freeUnits)}
        tone="text-success"
      />
      <StatItem
        icon={Activity}
        label="Занято"
        value={String(data.busyUnits)}
        tone="text-warning"
      />
      <StatItem
        icon={Clock}
        label="Средн. ETA"
        value={formatEta(data.avgEtaSeconds)}
        tone="text-info"
      />
    </div>
  );
}

export const HeaderStats = memo(HeaderStatsBase);
