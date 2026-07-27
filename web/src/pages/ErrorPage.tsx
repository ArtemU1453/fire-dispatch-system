import type { FallbackProps } from "react-error-boundary";
import { AlertTriangle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ApiErrorShape } from "@/types/api";

/** Fallback for the global React error boundary. */
export function ErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
  const api = error as Partial<ApiErrorShape>;
  const isNetwork = api?.code === "NETWORK";
  return (
    <div className="grid min-h-screen place-items-center bg-background p-6">
      <div className="max-w-md rounded-lg border border-border bg-card p-8 text-center">
        <div className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-full bg-danger/15 text-[hsl(var(--danger))]">
          <AlertTriangle className="h-7 w-7" />
        </div>
        <h1 className="text-xl font-bold">
          {isNetwork ? "Нет соединения с сервером" : "Произошла ошибка"}
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          {(error as Error)?.message ?? "Непредвиденная ошибка приложения."}
        </p>
        <Button className="mt-6" onClick={resetErrorBoundary}>
          <RotateCcw className="h-4 w-4" /> Повторить
        </Button>
      </div>
    </div>
  );
}
