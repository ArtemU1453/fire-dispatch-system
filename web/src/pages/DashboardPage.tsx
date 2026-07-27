import { Flame, Truck, Timer, Activity } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Panel } from "@/components/ui/panel";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";

const stats = [
  { icon: Flame, label: "Активные происшествия", value: "7", tone: "text-[hsl(var(--danger))]" },
  { icon: Truck, label: "Свободные подразделения", value: "24", tone: "text-success" },
  { icon: Activity, label: "Занятые подразделения", value: "11", tone: "text-[hsl(var(--warning))]" },
  { icon: Timer, label: "Среднее время прибытия", value: "6:12", tone: "text-info" },
];

const incidents = [
  { no: "2026-01847", type: "Пожар · жилой дом", addr: "ул. Ленина, 42", prio: "danger", status: "Работают", st: "danger" },
  { no: "2026-01846", type: "Возгорание · склад", addr: "Заводской пр., 7", prio: "danger", status: "В пути", st: "info" },
  { no: "2026-01845", type: "ДТП · два авто", addr: "пр. Мира, 45", prio: "warning", status: "Назначено", st: "warning" },
  { no: "2026-01842", type: "Срабатывание АПС", addr: "ТЦ «Восход»", prio: "success", status: "Локализовано", st: "success" },
] as const;

export function DashboardPage() {
  return (
    <div>
      <PageHeader title="Рабочее место диспетчера" description="Оперативная обстановка в реальном времени" />
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((s) => (
          <Card key={s.label}>
            <CardContent className="flex items-center gap-4 p-5">
              <div className={`grid h-12 w-12 place-items-center rounded-lg bg-secondary ${s.tone}`}>
                <s.icon className="h-6 w-6" />
              </div>
              <div>
                <div className="text-2xl font-bold tabular-nums">{s.value}</div>
                <div className="text-sm text-muted-foreground">{s.label}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      <Panel title="Активные происшествия" bodyClassName="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Номер</TableHead><TableHead>Тип</TableHead>
              <TableHead>Адрес</TableHead><TableHead>Приоритет</TableHead><TableHead>Статус</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {incidents.map((i) => (
              <TableRow key={i.no}>
                <TableCell className="font-mono text-muted-foreground">{i.no}</TableCell>
                <TableCell className="font-medium">{i.type}</TableCell>
                <TableCell className="text-muted-foreground">{i.addr}</TableCell>
                <TableCell><Badge variant={i.prio}>{i.prio === "danger" ? "Высокий" : i.prio === "warning" ? "Средний" : "Контроль"}</Badge></TableCell>
                <TableCell><Badge variant={i.st}>{i.status}</Badge></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Panel>
    </div>
  );
}
