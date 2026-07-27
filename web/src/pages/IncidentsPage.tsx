import { PageHeader } from "@/components/PageHeader";
import { Panel } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

export function IncidentsPage() {
  return (
    <div>
      <PageHeader
        title="Происшествия"
        description="Регистрация и ведение происшествий"
        actions={<Button><Plus className="h-4 w-4" /> Новое происшествие</Button>}
      />
      <Panel title="Реестр происшествий">
        <p className="text-sm text-muted-foreground">
          Раздел управления происшествиями. Реестр, карточки и фильтры подключаются
          к API происшествий на следующем этапе фронтенда.
        </p>
      </Panel>
    </div>
  );
}
