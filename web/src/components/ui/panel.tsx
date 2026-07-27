import * as React from "react";
import { cn } from "@/lib/utils";

/** Enterprise content panel with an optional titled header and actions. */
export interface PanelProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, "title"> {
  title?: React.ReactNode;
  actions?: React.ReactNode;
  bodyClassName?: string;
}

export const Panel = React.forwardRef<HTMLDivElement, PanelProps>(
  ({ title, actions, children, className, bodyClassName, ...props }, ref) => (
    <section
      ref={ref}
      className={cn("flex min-h-0 flex-col rounded-lg border border-border bg-panel text-panel-foreground shadow-sm", className)}
      {...props}
    >
      {(title || actions) && (
        <header className="flex items-center justify-between gap-3 border-b border-border px-5 py-3.5">
          <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{title}</div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </header>
      )}
      <div className={cn("min-h-0 flex-1 p-5", bodyClassName)}>{children}</div>
    </section>
  ),
);
Panel.displayName = "Panel";
