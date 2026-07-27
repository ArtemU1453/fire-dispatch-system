import { Map as MapIcon } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { Panel } from "@/components/ui/panel";

export function MapPage() {
  return (
    <div className="flex h-full flex-col">
      <PageHeader title="Карта" description="Оперативная обстановка на карте" />
      <Panel title="GIS-карта" className="flex-1" bodyClassName="p-0">
        <div className="grid h-full min-h-[420px] place-items-center text-center text-muted-foreground">
          <div>
            <MapIcon className="mx-auto mb-3 h-10 w-10 opacity-60" />
            <p className="text-sm">
              Библиотека карт <b>OpenLayers</b> подключена. Интерактивная GIS-карта
              будет реализована на следующем этапе.
            </p>
          </div>
        </div>
      </Panel>
    </div>
  );
}
