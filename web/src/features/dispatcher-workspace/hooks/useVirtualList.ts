/**
 * useVirtualList — a tiny, dependency-free fixed-height virtualizer.
 *
 * Renders only the rows intersecting the viewport (plus an overscan margin),
 * so the incident list stays smooth with thousands of records. Returns the
 * total spacer height, the visible slice, and a scroll handler.
 */
import { useCallback, useMemo, useState } from "react";

export interface VirtualRange<T> {
  /** Total scroll height of all rows. */
  totalHeight: number;
  /** Pixel offset of the first visible row (translateY of the inner list). */
  offsetY: number;
  /** The visible slice with absolute indices. */
  items: Array<{ index: number; item: T }>;
  onScroll: (e: { currentTarget: { scrollTop: number } }) => void;
}

export function useVirtualList<T>(
  items: T[],
  rowHeight: number,
  viewportHeight: number,
  overscan = 6,
): VirtualRange<T> {
  const [scrollTop, setScrollTop] = useState(0);

  const onScroll = useCallback(
    (e: { currentTarget: { scrollTop: number } }) => {
      setScrollTop(e.currentTarget.scrollTop);
    },
    [],
  );

  return useMemo<VirtualRange<T>>(() => {
    const count = items.length;
    const totalHeight = count * rowHeight;
    if (count === 0 || viewportHeight <= 0) {
      return { totalHeight, offsetY: 0, items: [], onScroll };
    }
    const first = Math.max(0, Math.floor(scrollTop / rowHeight) - overscan);
    const visibleCount = Math.ceil(viewportHeight / rowHeight) + overscan * 2;
    const last = Math.min(count, first + visibleCount);
    const slice: Array<{ index: number; item: T }> = [];
    for (let i = first; i < last; i += 1) slice.push({ index: i, item: items[i] });
    return { totalHeight, offsetY: first * rowHeight, items: slice, onScroll };
  }, [items, rowHeight, viewportHeight, overscan, scrollTop, onScroll]);
}
