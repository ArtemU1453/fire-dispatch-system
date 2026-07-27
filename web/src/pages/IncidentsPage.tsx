import { useNavigate } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { Panel } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

export function IncidentsPage() {
  const navigate = useNavigate();
  return (
    <div>
      <PageHeader
        title="Происшествия"
        description="Регистрация и ведение происшествий"
        actions={
          <Button onClick={() => navigate("/incidents/new")}>
            <Plus className="h-4 w-4" /> Новое происшествие
          </Button>
        }
      />
      <Panel title="Реестр происшествий">
        <p className="text-sm text-muted-foreground">
          Нажмите «Новое происшествие» (или клавишу F2), чтобы открыть форму
          регистрации: карточка, поиск адреса, GIS-обстановка, рекомендации AI,
          изменение состава сил и передача в Dispatch Engine.
        </p>
      </Panel>
    </div>
  );
}
