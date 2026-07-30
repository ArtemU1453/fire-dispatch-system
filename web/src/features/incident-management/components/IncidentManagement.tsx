/**
 * IncidentManagement — the operational management screen for one incident.
 * Four zones (card / map / resources / timeline) + quick-actions toolbar,
 * live via the incident realtime channel. Owns all modal state and hotkeys.
 */
import { memo, useCallback, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ConnectionStatus } from "@/features/dispatcher-workspace/components/ConnectionStatus";
import { IncidentCard } from "./IncidentCard";
import { IncidentMap } from "./IncidentMap";
import { ResourcesPanel } from "./ResourcesPanel";
import { OperationalTimeline } from "./OperationalTimeline";
import { QuickActions } from "./QuickActions";
import {
  AddResourceModal,
  ReplaceResourceModal,
  UnitCardModal,
} from "./ResourceManager";
import {
  ChangeLevelModal,
  CloseIncidentModal,
  MessageModal,
  TransferModal,
} from "./QuickActionModals";
import {
  useAssignedResources,
  useIncidentRealtime,
  useManagementHotkeys,
} from "../hooks";
import { useManagementStore } from "../store/management.store";
import type { AssignedResource } from "../types";

function IncidentManagementBase({ incidentId }: { incidentId: string }) {
  const navigate = useNavigate();
  const { status } = useIncidentRealtime(incidentId);
  const { resources } = useAssignedResources(incidentId);
  const selectedResourceId = useManagementStore((s) => s.selectedResourceId);

  const [addOpen, setAddOpen] = useState(false);
  const [addReserve, setAddReserve] = useState(false);
  const [replaceTarget, setReplaceTarget] = useState<AssignedResource | null>(null);
  const [viewTarget, setViewTarget] = useState<AssignedResource | null>(null);
  const [closeOpen, setCloseOpen] = useState(false);
  const [messageOpen, setMessageOpen] = useState(false);
  const [levelOpen, setLevelOpen] = useState(false);
  const [transferOpen, setTransferOpen] = useState(false);

  const assignedIds = useMemo(
    () => resources.map((r) => r.unitId ?? r.resourceId),
    [resources],
  );

  const openAdd = useCallback(() => {
    setAddReserve(false);
    setAddOpen(true);
  }, []);
  const openAddReserve = useCallback(() => {
    setAddReserve(true);
    setAddOpen(true);
  }, []);
  const openReplaceSelected = useCallback(() => {
    const target =
      resources.find((r) => r.resourceId === selectedResourceId) ?? resources[0] ?? null;
    if (target) setReplaceTarget(target);
  }, [resources, selectedResourceId]);
  const print = useCallback(() => window.print(), []);

  useManagementHotkeys({
    onAddResource: openAdd,
    onReplace: openReplaceSelected,
    onClose: () => setCloseOpen(true),
    onPrint: print,
  });

  return (
    <div className="flex h-full min-h-0 flex-col gap-2">
      {/* Toolbar */}
      <header className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-panel px-3 py-2">
        <h1 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
          Управление происшествием
        </h1>
        <QuickActions
          onAddResource={openAdd}
          onChangeLevel={() => setLevelOpen(true)}
          onTransfer={() => setTransferOpen(true)}
          onMessage={() => setMessageOpen(true)}
          onPrint={print}
          onClose={() => setCloseOpen(true)}
        />
        <ConnectionStatus status={status} />
      </header>

      {/* Card / Map / Resources */}
      <div className="grid min-h-0 flex-1 grid-cols-1 gap-2 xl:grid-cols-[minmax(300px,340px)_1fr_minmax(360px,460px)]">
        <div className="hidden min-h-0 xl:block">
          <IncidentCard incidentId={incidentId} />
        </div>
        <div className="min-h-0">
          <IncidentMap incidentId={incidentId} />
        </div>
        <div className="hidden min-h-0 xl:block">
          <ResourcesPanel
            incidentId={incidentId}
            onReplace={setReplaceTarget}
            onViewCard={setViewTarget}
            onAddReserve={openAddReserve}
          />
        </div>
      </div>

      {/* Timeline */}
      <div className="h-[200px] shrink-0">
        <OperationalTimeline incidentId={incidentId} />
      </div>

      {/* Modals */}
      <AddResourceModal
        incidentId={incidentId}
        open={addOpen}
        onOpenChange={setAddOpen}
        assignedIds={assignedIds}
        reserve={addReserve}
      />
      <ReplaceResourceModal
        incidentId={incidentId}
        open={replaceTarget !== null}
        onOpenChange={(o) => !o && setReplaceTarget(null)}
        target={replaceTarget}
        assignedIds={assignedIds}
      />
      <UnitCardModal
        open={viewTarget !== null}
        onOpenChange={(o) => !o && setViewTarget(null)}
        resource={viewTarget}
      />
      <CloseIncidentModal
        incidentId={incidentId}
        open={closeOpen}
        onOpenChange={setCloseOpen}
        onClosed={() => navigate("/dashboard")}
      />
      <MessageModal incidentId={incidentId} open={messageOpen} onOpenChange={setMessageOpen} />
      <ChangeLevelModal incidentId={incidentId} open={levelOpen} onOpenChange={setLevelOpen} />
      <TransferModal incidentId={incidentId} open={transferOpen} onOpenChange={setTransferOpen} />
    </div>
  );
}

export const IncidentManagement = memo(IncidentManagementBase);
