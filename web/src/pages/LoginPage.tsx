import { Navigate } from "react-router-dom";
import { ShieldAlert } from "lucide-react";
import { LoginForm } from "@/features/auth/LoginForm";
import { useAuthStore } from "@/store/auth.store";
import { paths } from "@/routes/paths";

export function LoginPage() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (isAuthenticated) return <Navigate to={paths.dashboard} replace />;

  return (
    <div className="grid min-h-screen place-items-center bg-background p-6">
      <div
        className="pointer-events-none fixed inset-0 opacity-60"
        style={{
          background:
            "radial-gradient(60% 50% at 50% 40%, hsl(var(--accent)/0.10), transparent 70%)",
        }}
      />
      <div className="relative w-full max-w-md rounded-lg border border-border bg-card p-8 shadow-2xl">
        <div className="mb-7 flex items-center gap-3">
          <div className="grid h-12 w-12 place-items-center rounded-lg bg-primary/15 text-primary">
            <ShieldAlert className="h-6 w-6" />
          </div>
          <div>
            <div className="text-lg font-bold tracking-wide">
              AI Dispatcher <span className="text-primary">МЧС</span>
            </div>
            <div className="text-xs text-muted-foreground">
              Автоматизированная система управления выездом
            </div>
          </div>
        </div>
        <LoginForm />
        <p className="mt-6 text-center text-xs text-muted-foreground">
          v1.0 Enterprise · Build 2026.07
        </p>
      </div>
    </div>
  );
}
