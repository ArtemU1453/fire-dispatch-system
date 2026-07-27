import { PageHeader } from "@/components/PageHeader";
import { Panel } from "@/components/ui/panel";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export function ReportsPage() {
  return (
    <div>
      <PageHeader title="Аналитика" description="KPI, статистика и отчёты" />
      <Panel title="Аналитические показатели">
        <Tabs defaultValue="kpi">
          <TabsList>
            <TabsTrigger value="kpi">KPI</TabsTrigger>
            <TabsTrigger value="stats">Статистика</TabsTrigger>
            <TabsTrigger value="reports">Отчёты</TabsTrigger>
          </TabsList>
          <TabsContent value="kpi">
            <p className="text-sm text-muted-foreground">Ключевые показатели подключаются к модулю Operational Intelligence.</p>
          </TabsContent>
          <TabsContent value="stats">
            <p className="text-sm text-muted-foreground">Распределения и динамика вызовов — на следующем этапе.</p>
          </TabsContent>
          <TabsContent value="reports">
            <p className="text-sm text-muted-foreground">Формирование и экспорт отчётов — на следующем этапе.</p>
          </TabsContent>
        </Tabs>
      </Panel>
    </div>
  );
}
