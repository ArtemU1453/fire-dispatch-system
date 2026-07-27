import * as ToastPrimitive from "@radix-ui/react-toast";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import { useToast, type ToastVariant } from "./use-toast";

const variantClass: Record<ToastVariant, string> = {
  default: "border-border",
  success: "border-success/50",
  warning: "border-warning/50",
  danger: "border-danger/50",
  info: "border-info/50",
};

/** Global toast host — render once at the app root. */
export function Toaster() {
  const toasts = useToast((s) => s.toasts);
  const dismiss = useToast((s) => s.dismiss);
  return (
    <ToastPrimitive.Provider swipeDirection="right">
      {toasts.map((t) => (
        <ToastPrimitive.Root
          key={t.id}
          onOpenChange={(open) => !open && dismiss(t.id)}
          className={cn(
            "pointer-events-auto flex w-full items-start gap-3 rounded-md border-l-4 bg-card p-4 shadow-xl data-[state=open]:animate-fade-in",
            variantClass[t.variant],
          )}
        >
          <div className="flex-1">
            {t.title && <ToastPrimitive.Title className="text-sm font-semibold">{t.title}</ToastPrimitive.Title>}
            {t.description && (
              <ToastPrimitive.Description className="mt-1 text-sm text-muted-foreground">
                {t.description}
              </ToastPrimitive.Description>
            )}
          </div>
          <ToastPrimitive.Close className="text-muted-foreground hover:text-foreground">
            <X className="h-4 w-4" />
          </ToastPrimitive.Close>
        </ToastPrimitive.Root>
      ))}
      <ToastPrimitive.Viewport className="fixed bottom-4 right-4 z-[100] flex w-96 max-w-[calc(100vw-2rem)] flex-col gap-2 outline-none" />
    </ToastPrimitive.Provider>
  );
}
