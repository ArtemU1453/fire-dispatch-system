import { Moon, Sun, PanelLeft, Bell } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { Panel } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";
import { useSettingsStore } from "@/store/settings.store";
import { useToast } from "@/components/ui/use-toast";

export function SettingsPage() {
  const theme = useSettingsStore((s) => s.theme);
  const setTheme = useSettingsStore((s) => s.setTheme);
  const toggleSidebar = useSettingsStore((s) => s.toggleSidebar);
  const toast = useToast((s) => s.toast);

  return (
    <div>
      <PageHeader title="Настройки" description="Персональные настройки интерфейса" />
      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="Оформление">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium">Тема оформления</div>
              <div className="text-sm text-muted-foreground">Тёмная тема — по умолчанию</div>
            </div>
            <div className="flex gap-2">
              <Button variant={theme === "dark" ? "default" : "outline"} size="sm" onClick={() => setTheme("dark")}>
                <Moon className="h-4 w-4" /> Тёмная
              </Button>
              <Button variant={theme === "light" ? "default" : "outline"} size="sm" onClick={() => setTheme("light")}>
                <Sun className="h-4 w-4" /> Светлая
              </Button>
            </div>
          </div>
          <div className="mt-5 flex items-center justify-between border-t border-border pt-5">
            <div>
              <div className="text-sm font-medium">Боковая панель</div>
              <div className="text-sm text-muted-foreground">Свернуть/развернуть навигацию</div>
            </div>
            <Button variant="outline" size="sm" onClick={toggleSidebar}>
              <PanelLeft className="h-4 w-4" /> Переключить
            </Button>
          </div>
        </Panel>
        <Panel title="Уведомления">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium">Проверка уведомлений</div>
              <div className="text-sm text-muted-foreground">Показать тестовое уведомление</div>
            </div>
            <Button variant="outline" size="sm" onClick={() => toast({ variant: "info", title: "Тест", description: "Уведомление работает" })}>
              <Bell className="h-4 w-4" /> Показать
            </Button>
          </div>
        </Panel>
      </div>
    </div>
  );
}
