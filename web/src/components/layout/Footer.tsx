export function Footer() {
  return (
    <footer
      className="flex shrink-0 items-center justify-between border-t border-border bg-panel px-5 text-xs text-muted-foreground"
      style={{ height: "var(--footer-height)" }}
    >
      <div className="flex items-center gap-2">
        <span>© МЧС</span><span className="opacity-40">•</span>
        <span>AI Dispatcher</span><span className="opacity-40">•</span>
        <span>Enterprise Edition</span>
      </div>
      <div className="flex items-center gap-4">
        <span className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-success animate-pulseglow" /> Соединение устойчивое
        </span>
        <span className="tabular-nums">v1.0 · Build 2026.07</span>
      </div>
    </footer>
  );
}
