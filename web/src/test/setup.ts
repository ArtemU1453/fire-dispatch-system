import "@testing-library/jest-dom/vitest";

// --- jsdom polyfills used by the dispatcher workspace --------------------------

// ResizeObserver (IncidentList measures its viewport for virtual scrolling).
class ResizeObserverMock {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
if (!("ResizeObserver" in globalThis)) {
  (globalThis as unknown as { ResizeObserver: unknown }).ResizeObserver =
    ResizeObserverMock;
}

// matchMedia (used by theme-aware components).
if (!window.matchMedia) {
  window.matchMedia = ((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener: () => {},
    removeEventListener: () => {},
    addListener: () => {},
    removeListener: () => {},
    dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia;
}
