import { useNavigate } from "react-router-dom";
import { Compass } from "lucide-react";
import { Button } from "@/components/ui/button";
import { paths } from "@/routes/paths";

export function NotFoundPage() {
  const navigate = useNavigate();
  return (
    <div className="grid min-h-screen place-items-center bg-background p-6">
      <div className="max-w-md text-center">
        <div className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-full bg-secondary text-muted-foreground">
          <Compass className="h-7 w-7" />
        </div>
        <div className="text-5xl font-black tracking-tight">404</div>
        <p className="mt-2 text-muted-foreground">Страница не найдена</p>
        <Button className="mt-6" variant="outline" onClick={() => navigate(paths.dashboard)}>
          На рабочее место
        </Button>
      </div>
    </div>
  );
}
