import { PageHeader } from "@/components/PageHeader";
import { Panel } from "@/components/ui/panel";

export function JournalPage() {
  return (
    <div>
      <PageHeader title="Журнал" description="Журнал событий и действий" />
      <Panel title="Журнал событий">
        <p className="text-sm text-muted-foreground">
          Единый журнал оперативных событий подключается к API наблюдаемости и
          журналирования на следующем этапе.
        </p>
      </Panel>
    </div>
  );
}
