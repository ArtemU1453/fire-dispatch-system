/**
 * DispatcherWorkspace — the five-zone operational layout:
 *   ┌───────────────── top: KPI strip + live-channel status ─────────────────┐
 *   │ left: IncidentList │ center: OperationalMap │ right: IncidentDetails    │
 *   └───────────────────────── bottom: OperationalLog ───────────────────────┘
 *
 * Mounts the real-time channel (`useDispatcherSocket`) for the whole screen.
 */
import { memo } from "react";
import { HeaderStats } from "./HeaderStats";
import { ConnectionStatus } from "./ConnectionStatus";
import { IncidentList } from "./IncidentList";
import { OperationalMap } from "./OperationalMap";
import { IncidentDetails } from "./IncidentDetails";
import { OperationalLog } from "./OperationalLog";
import { useDispatcherSocket } from "../hooks";

function DispatcherWorkspaceBase() {
  const { status } = useDispatcherSocket();

  return (
    <div className="flex h-full min-h-0 flex-col gap-2">
      {/* Zone 1 — top operational bar */}
      <header className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-panel px-3 py-2">
        <div className="flex items-center gap-2">
          <h1 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
            Рабочее место диспетчера
          </h1>
        </div>
        <HeaderStats />
        <ConnectionStatus status={status} />
      </header>

      {/* Zones 2–4 — list / map / details */}
      <div className="grid min-h-0 flex-1 grid-cols-1 gap-2 lg:grid-cols-[340px_1fr_380px]">
        <div className="hidden min-h-0 lg:block">
          <IncidentList />
        </div>
        <div className="min-h-0">
          <OperationalMap />
        </div>
        <div className="hidden min-h-0 lg:block">
          <IncidentDetails />
        </div>
      </div>

      {/* Zone 5 — event log */}
      <div className="h-[220px] shrink-0">
        <OperationalLog />
      </div>
    </div>
  );
}

export const DispatcherWorkspace = memo(DispatcherWorkspaceBase);
