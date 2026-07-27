/**
 * IncidentList — the left operational panel: live active incidents with search,
 * filtering, sorting and windowed (virtual) scrolling for large volumes.
 */
import { memo, useCallback, useEffect, useRef, useState } from "react";
import { AlertCircle, Inbox } from "lucide-react";
import { Panel } from "@/components/ui/panel";
import { Loader } from "@/components/ui/loader";
import { Button } from "@/components/ui/button";
import { IncidentFilters } from "./IncidentFilters";
import { IncidentListItem } from "./IncidentListItem";
import { useFilteredIncidents, useVirtualList } from "../hooks";
import { useDispatcherStore } from "../store/dispatcher.store";

const ROW_HEIGHT = 108;

function IncidentListBase() {
  const { incidents, total, isLoading, isError, refetch } = useFilteredIncidents();
  const selectedId = useDispatcherStore((s) => s.selectedIncidentId);
  const selectIncident = useDispatcherStore((s) => s.selectIncident);
  const requestFlyTo = useDispatcherStore((s) => s.requestFlyTo);

  const scrollRef = useRef<HTMLDivElement>(null);
  const [viewport, setViewport] = useState(600);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    // Keep the sensible default until a real (non-zero) height is measured;
    // environments without layout (jsdom) report 0 and would render no rows.
    const update = () => {
      if (el.clientHeight > 0) setViewport(el.clientHeight);
    };
    update();
    const observer = new ResizeObserver(update);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const { totalHeight, offsetY, items, onScroll } = useVirtualList(
    incidents,
    ROW_HEIGHT,
    viewport,
  );

  const handleSelect = useCallback((id: string) => selectIncident(id), [selectIncident]);
  const handleLocate = useCallback((id: string) => requestFlyTo(id), [requestFlyTo]);

  return (
    <Panel
      title={`Происшествия · ${incidents.length}${
        incidents.length !== total ? ` из ${total}` : ""
      }`}
      className="h-full"
      bodyClassName="flex min-h-0 flex-col p-0"
    >
      <IncidentFilters />

      <div
        ref={scrollRef}
        onScroll={onScroll}
        className="min-h-0 flex-1 overflow-y-auto"
        role="listbox"
        aria-label="Список активных происшествий"
        aria-busy={isLoading}
      >
        {isLoading ? (
          <div className="flex h-full items-center justify-center">
            <Loader label="Загрузка происшествий…" />
          </div>
        ) : isError ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 p-6 text-center">
            <AlertCircle className="h-8 w-8 text-danger" aria-hidden />
            <p className="text-sm text-muted-foreground">
              Не удалось загрузить список происшествий.
            </p>
            <Button size="sm" variant="outline" onClick={() => refetch()}>
              Повторить
            </Button>
          </div>
        ) : incidents.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-2 p-6 text-center text-muted-foreground">
            <Inbox className="h-8 w-8" aria-hidden />
            <p className="text-sm">Нет активных происшествий по фильтру.</p>
          </div>
        ) : (
          <div style={{ height: totalHeight, position: "relative" }}>
            <div style={{ transform: `translateY(${offsetY}px)` }}>
              {items.map(({ item }) => (
                <IncidentListItem
                  key={item.id}
                  incident={item}
                  selected={item.id === selectedId}
                  onSelect={handleSelect}
                  onLocate={handleLocate}
                  style={{ height: ROW_HEIGHT }}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </Panel>
  );
}

export const IncidentList = memo(IncidentListBase);
