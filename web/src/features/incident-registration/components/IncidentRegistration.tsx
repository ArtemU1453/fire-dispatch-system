/**
 * IncidentRegistration — orchestrates the full workflow:
 *   card (form) + address → GIS → AI preview → force selection → confirm →
 *   Dispatch Engine → dashboard auto-refresh.
 *
 * Three working columns plus a persistent action bar. Hotkeys: Ctrl+Enter to
 * confirm, Esc to cancel.
 */
import { memo, useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Eraser, Send, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { IncidentForm } from "./IncidentForm";
import { AddressSearch } from "./AddressSearch";
import { RegistrationMap } from "./RegistrationMap";
import { DispatchPreview } from "./DispatchPreview";
import { ResourceSelection } from "./ResourceSelection";
import { ConfirmDispatchModal } from "./ConfirmDispatchModal";
import { useConfirmRegistration, useRegistrationHotkeys } from "../hooks";
import { useRegistrationStore } from "../store/registration.store";

function IncidentRegistrationBase() {
  const navigate = useNavigate();
  const [confirmOpen, setConfirmOpen] = useState(false);

  const reset = useRegistrationStore((s) => s.reset);
  const location = useRegistrationStore((s) => s.location);
  const incidentTypeId = useRegistrationStore((s) => s.form.incidentTypeId);

  // Start from a clean slate each time the page mounts.
  useEffect(() => {
    reset();
    return () => reset();
  }, [reset]);

  const confirm = useConfirmRegistration(() => {
    setConfirmOpen(false);
    navigate("/dashboard");
  });

  const canConfirm = Boolean(location && incidentTypeId);

  const openConfirm = useCallback(() => {
    if (canConfirm) setConfirmOpen(true);
  }, [canConfirm]);

  const cancel = useCallback(() => {
    if (confirmOpen) {
      setConfirmOpen(false);
      return;
    }
    navigate("/dashboard");
  }, [confirmOpen, navigate]);

  useRegistrationHotkeys({
    onConfirm: () => (confirmOpen ? confirm.mutate() : openConfirm()),
    onCancel: cancel,
  });

  return (
    <div className="flex h-full min-h-0 flex-col gap-2">
      <div className="grid min-h-0 flex-1 grid-cols-1 gap-2 xl:grid-cols-[minmax(340px,380px)_1fr_minmax(340px,400px)]">
        {/* Left — card + address */}
        <div className="min-h-0 overflow-y-auto rounded-lg border border-border bg-panel p-4">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
            Новое происшествие
          </h2>
          <div className="flex flex-col gap-4">
            <AddressSearch />
            <IncidentForm />
          </div>
        </div>

        {/* Center — GIS */}
        <div className="hidden min-h-0 xl:block">
          <RegistrationMap />
        </div>

        {/* Right — AI preview + force selection */}
        <div className="grid min-h-0 grid-rows-2 gap-2">
          <div className="min-h-0">
            <DispatchPreview />
          </div>
          <div className="min-h-0">
            <ResourceSelection />
          </div>
        </div>
      </div>

      {/* Action bar */}
      <div className="flex shrink-0 items-center justify-between rounded-lg border border-border bg-panel px-4 py-2.5">
        <p className="text-xs text-muted-foreground">
          F2 — новый вызов · Ctrl+Enter — подтвердить · Esc — отмена
        </p>
        <div className="flex items-center gap-2">
          <Button variant="ghost" onClick={() => reset()}>
            <Eraser className="mr-1.5 h-4 w-4" aria-hidden />
            Очистить форму
          </Button>
          <Button variant="outline" onClick={cancel}>
            <X className="mr-1.5 h-4 w-4" aria-hidden />
            Отмена
          </Button>
          <Button onClick={openConfirm} disabled={!canConfirm}>
            <Send className="mr-1.5 h-4 w-4" aria-hidden />
            Передать в Dispatch Engine
          </Button>
        </div>
      </div>

      <ConfirmDispatchModal
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        onConfirm={() => confirm.mutate()}
        isSubmitting={confirm.isPending}
      />
    </div>
  );
}

export const IncidentRegistration = memo(IncidentRegistrationBase);
