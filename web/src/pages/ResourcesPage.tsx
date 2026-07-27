import { PageHeader } from "@/components/PageHeader";
import { Panel } from "@/components/ui/panel";

export function ResourcesPage() {
  return (
    <div>
      <PageHeader title="Подразделения" description="Силы и средства гарнизона" />
      <Panel title="Подразделения и техника">
        <p className="text-sm text-muted-foreground">
          Раздел управления подразделениями: статусы, местоположение и загруженность
          подключаются к модулю Resource Management на следующем этапе.
        </p>
      </Panel>
    </div>
  );
}
