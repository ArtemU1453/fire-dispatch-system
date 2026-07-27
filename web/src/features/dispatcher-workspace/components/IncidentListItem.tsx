/**
 * IncidentListItem — a single incident card in the left panel. Memoized: it
 * only re-renders when its incident or selection state changes.
 */
import { memo } from "react";
import { MapPin, Clock, Users } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import {
  categoryLabel,
  priorityColor,
  priorityLabel,
  priorityVariant,
  statusLabel,
  timeAgo,
} from "../utils/format";
import type { IncidentSummary } from "../types";

interface Props {
  incident: IncidentSummary;
  selected: boolean;
  onSelect: (id: string) => void;
  onLocate: (id: string) => void;
  style?: React.CSSProperties;
}

function IncidentListItemBase({ incident, selected, onSelect, onLocate, style }: Props) {
  return (
    <div
      style={style}
      role="option"
      aria-selected={selected}
      tabIndex={0}
      onClick={() => onSelect(incident.id)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect(incident.id);
        }
      }}
      className={cn(
        "group relative flex cursor-pointer flex-col gap-1.5 border-b border-border px-3 py-2.5 outline-none transition-colors",
        "hover:bg-muted/50 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring",
        selected && "bg-muted",
      )}
    >
      <span
        aria-hidden
        className="absolute left-0 top-0 h-full w-1"
        style={{ backgroundColor: priorityColor(incident.priority) }}
      />
      <div className="flex items-center justify-between gap-2 pl-1.5">
        <span className="truncate text-sm font-semibold">№ {incident.number}</span>
        <Badge variant={priorityVariant(incident.priority)} className="shrink-0">
          {priorityLabel(incident.priority)}
        </Badge>
      </div>

      <div className="flex items-center justify-between gap-2 pl-1.5 text-xs">
        <span className="truncate font-medium text-foreground/90">
          {categoryLabel(incident.category)}
        </span>
        <span className="shrink-0 text-muted-foreground">{statusLabel(incident.status)}</span>
      </div>

      {incident.address && (
        <div className="flex items-center gap-1 pl-1.5 text-xs text-muted-foreground">
          <MapPin className="h-3 w-3 shrink-0" aria-hidden />
          <span className="truncate">{incident.address}</span>
        </div>
      )}

      <div className="flex items-center justify-between gap-2 pl-1.5 text-[11px] text-muted-foreground">
        <span className="flex items-center gap-1">
          <Clock className="h-3 w-3" aria-hidden />
          {timeAgo(incident.reported_at)}
        </span>
        <span className="flex items-center gap-2">
          {typeof incident.assigned_count === "number" && (
            <span className="flex items-center gap-1">
              <Users className="h-3 w-3" aria-hidden />
              {incident.assigned_count}
            </span>
          )}
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onLocate(incident.id);
            }}
            className="rounded px-1 py-0.5 text-info hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label={`Показать № ${incident.number} на карте`}
          >
            На карте
          </button>
        </span>
      </div>
    </div>
  );
}

export const IncidentListItem = memo(IncidentListItemBase);
