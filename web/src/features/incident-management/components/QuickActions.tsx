/**
 * Quick-actions toolbar for the management screen.
 */
import { memo } from "react";
import {
  Plus,
  ArrowUpDown,
  UserCog,
  MessageSquarePlus,
  Printer,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface Props {
  onAddResource: () => void;
  onChangeLevel: () => void;
  onTransfer: () => void;
  onMessage: () => void;
  onPrint: () => void;
  onClose: () => void;
}

function QuickActionsBase(props: Props) {
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <Button size="sm" variant="outline" onClick={props.onAddResource}>
        <Plus className="mr-1 h-3.5 w-3.5" aria-hidden /> Добавить
      </Button>
      <Button size="sm" variant="outline" onClick={props.onChangeLevel}>
        <ArrowUpDown className="mr-1 h-3.5 w-3.5" aria-hidden /> Уровень
      </Button>
      <Button size="sm" variant="outline" onClick={props.onTransfer}>
        <UserCog className="mr-1 h-3.5 w-3.5" aria-hidden /> Руководителю
      </Button>
      <Button size="sm" variant="outline" onClick={props.onMessage}>
        <MessageSquarePlus className="mr-1 h-3.5 w-3.5" aria-hidden /> Сообщение
      </Button>
      <Button size="sm" variant="outline" onClick={props.onPrint}>
        <Printer className="mr-1 h-3.5 w-3.5" aria-hidden /> Печать
      </Button>
      <Button size="sm" variant="success" onClick={props.onClose}>
        <CheckCircle2 className="mr-1 h-3.5 w-3.5" aria-hidden /> Закрыть
      </Button>
    </div>
  );
}

export const QuickActions = memo(QuickActionsBase);
