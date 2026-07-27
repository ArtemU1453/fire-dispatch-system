/**
 * MapLayerManager — a compact overlay panel to toggle map layers on/off.
 */
import { memo } from "react";
import { Layers } from "lucide-react";
import { cn } from "@/lib/utils";
import { useDispatcherStore } from "../store/dispatcher.store";
import type { MapLayerId } from "../types";

const LAYERS: Array<{ id: MapLayerId; label: string }> = [
  { id: "incidents", label: "Происшествия" },
  { id: "units", label: "Подразделения" },
  { id: "routes", label: "Маршруты" },
  { id: "zones", label: "Зоны ответственности" },
  { id: "hydrants", label: "Гидранты" },
  { id: "water_sources", label: "Водоисточники" },
  { id: "closed_roads", label: "Закрытые дороги" },
];

function MapLayerManagerBase({ className }: { className?: string }) {
  const layers = useDispatcherStore((s) => s.map.layers);
  const toggleLayer = useDispatcherStore((s) => s.toggleLayer);

  return (
    <div
      className={cn(
        "w-52 rounded-lg border border-border bg-panel/95 p-2 shadow-lg backdrop-blur",
        className,
      )}
      role="group"
      aria-label="Слои карты"
    >
      <div className="mb-1.5 flex items-center gap-1.5 px-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
        <Layers className="h-3.5 w-3.5" aria-hidden />
        Слои карты
      </div>
      <ul className="flex flex-col">
        {LAYERS.map((layer) => (
          <li key={layer.id}>
            <label className="flex cursor-pointer items-center gap-2 rounded px-1 py-1 text-xs hover:bg-muted/60">
              <input
                type="checkbox"
                checked={layers[layer.id]}
                onChange={() => toggleLayer(layer.id)}
                className="h-3.5 w-3.5 accent-[hsl(var(--primary))]"
              />
              <span>{layer.label}</span>
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
}

export const MapLayerManager = memo(MapLayerManagerBase);
