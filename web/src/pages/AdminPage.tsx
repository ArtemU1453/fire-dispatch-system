import { PageHeader } from "@/components/PageHeader";
import { Panel } from "@/components/ui/panel";

export function AdminPage() {
  return (
    <div>
      <PageHeader title="Администрирование" description="Пользователи, роли и настройки системы" />
      <Panel title="Администрирование системы">
        <p className="text-sm text-muted-foreground">
          Управление пользователями, ролями (RBAC), справочниками и интеграциями
          подключается к модулю Administration на следующем этапе.
        </p>
      </Panel>
    </div>
  );
}
