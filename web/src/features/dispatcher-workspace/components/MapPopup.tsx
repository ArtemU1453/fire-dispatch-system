/**
 * MapPopup — content rendered inside the OpenLayers overlay when a feature is
 * clicked. Kept presentational; positioning is handled by the map component.
 */
import { memo } from "react";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { MapPointFeature } from "../types";

interface Props {
  feature: MapPointFeature;
  onClose: () => void;
  onOpenIncident?: (incidentId: string) => void;
}

function MapPopupBase({ feature, onClose, onOpenIncident }: Props) {
  const incidentId =
    feature.kind === "incident" ? feature.id.replace("incident:", "") : null;

  return (
    <div className="min-w-[200px] max-w-[260px] rounded-lg border border-border bg-panel p-3 shadow-xl">
      <div className="mb-1.5 flex items-start justify-between gap-2">
        <span className="text-sm font-semibold">{feature.label}</span>
        <button
          type="button"
          onClick={onClose}
          aria-label="Закрыть"
          className="rounded p-0.5 text-muted-foreground hover:text-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <X className="h-3.5 w-3.5" aria-hidden />
        </button>
      </div>

      {feature.meta && (
        <dl className="flex flex-col gap-0.5 text-xs">
          {Object.entries(feature.meta)
            .filter(([, v]) => v != null && v !== "")
            .map(([k, v]) => (
              <div key={k} className="flex justify-between gap-3">
                <dt className="text-muted-foreground">{k}</dt>
                <dd className="truncate text-right font-medium">{String(v)}</dd>
              </div>
            ))}
        </dl>
      )}

      {incidentId && onOpenIncident && (
        <Button
          size="sm"
          variant="outline"
          className="mt-2 w-full"
          onClick={() => onOpenIncident(incidentId)}
        >
          Открыть карточку
        </Button>
      )}
    </div>
  );
}

export const MapPopup = memo(MapPopupBase);
