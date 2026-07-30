/**
 * Quick-action modals: close incident, send message, change call level,
 * transfer to a commander. Each performs a real backend operation.
 */
import { memo, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { useIncident, useManagementActions } from "../hooks";
import { statusLabel } from "../utils";
import type { IncidentStatus } from "../types";

const PRIORITIES: Array<{ value: string; label: string }> = [
  { value: "low", label: "Низкий" },
  { value: "normal", label: "Обычный" },
  { value: "high", label: "Высокий" },
  { value: "critical", label: "Критический" },
];

export const CloseIncidentModal = memo(function CloseIncidentModal({
  incidentId,
  open,
  onOpenChange,
  onClosed,
}: {
  incidentId: string;
  open: boolean;
  onOpenChange: (o: boolean) => void;
  onClosed: () => void;
}) {
  const { data: incident } = useIncident(incidentId);
  const { close } = useManagementActions(incidentId);
  const [status, setStatus] = useState<IncidentStatus | "">("");
  const [note, setNote] = useState("");

  const options = incident?.allowed_transitions ?? [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Закрыть / изменить статус происшествия</DialogTitle>
        </DialogHeader>
        {options.length === 0 ? (
          <p className="text-sm text-muted-foreground">Нет доступных переходов статуса.</p>
        ) : (
          <div className="flex flex-col gap-3">
            <Select value={status} onValueChange={(v) => setStatus(v as IncidentStatus)}>
              <SelectTrigger aria-label="Новый статус">
                <SelectValue placeholder="Выберите статус…" />
              </SelectTrigger>
              <SelectContent>
                {options.map((s) => (
                  <SelectItem key={s} value={s}>{statusLabel(s)}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={2}
              placeholder="Примечание (необязательно)"
              className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => onOpenChange(false)}>Отмена</Button>
              <Button
                disabled={!status || close.isPending}
                onClick={() =>
                  status &&
                  close.mutate(
                    { status, note: note || undefined },
                    { onSuccess: () => { onOpenChange(false); onClosed(); } },
                  )
                }
              >
                {close.isPending ? "Применение…" : "Применить"}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
});

export const MessageModal = memo(function MessageModal({
  incidentId,
  open,
  onOpenChange,
}: {
  incidentId: string;
  open: boolean;
  onOpenChange: (o: boolean) => void;
}) {
  const { addMessage } = useManagementActions(incidentId);
  const [text, setText] = useState("");
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Создать сообщение</DialogTitle>
        </DialogHeader>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={4}
          placeholder="Текст сообщения диспетчера…"
          className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>Отмена</Button>
          <Button
            disabled={!text.trim() || addMessage.isPending}
            onClick={() =>
              addMessage.mutate(text.trim(), {
                onSuccess: () => { setText(""); onOpenChange(false); },
              })
            }
          >
            {addMessage.isPending ? "Отправка…" : "Добавить"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
});

export const ChangeLevelModal = memo(function ChangeLevelModal({
  incidentId,
  open,
  onOpenChange,
}: {
  incidentId: string;
  open: boolean;
  onOpenChange: (o: boolean) => void;
}) {
  const { changeLevel } = useManagementActions(incidentId);
  const [priority, setPriority] = useState("");
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Изменить уровень вызова</DialogTitle>
        </DialogHeader>
        <Select value={priority} onValueChange={setPriority}>
          <SelectTrigger aria-label="Уровень вызова">
            <SelectValue placeholder="Выберите уровень…" />
          </SelectTrigger>
          <SelectContent>
            {PRIORITIES.map((p) => (
              <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <div className="mt-3 flex justify-end gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>Отмена</Button>
          <Button
            disabled={!priority || changeLevel.isPending}
            onClick={() =>
              changeLevel.mutate(priority, { onSuccess: () => onOpenChange(false) })
            }
          >
            {changeLevel.isPending ? "Изменение…" : "Применить"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
});

export const TransferModal = memo(function TransferModal({
  incidentId,
  open,
  onOpenChange,
}: {
  incidentId: string;
  open: boolean;
  onOpenChange: (o: boolean) => void;
}) {
  const { addMessage } = useManagementActions(incidentId);
  const [name, setName] = useState("");
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Передать руководителю</DialogTitle>
        </DialogHeader>
        <Input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="ФИО руководителя тушения"
          aria-label="Руководитель"
        />
        <div className="mt-3 flex justify-end gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>Отмена</Button>
          <Button
            disabled={!name.trim() || addMessage.isPending}
            onClick={() =>
              addMessage.mutate(`Управление передано руководителю: ${name.trim()}`, {
                onSuccess: () => { setName(""); onOpenChange(false); },
              })
            }
          >
            Передать
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
});
