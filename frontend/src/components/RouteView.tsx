import { Polyline, Tooltip } from 'react-leaflet';

import type { RouteResponse } from '../types/api';
import { formatDistance, formatDuration } from '../utils/format';

export interface RouteViewProps {
  route: RouteResponse;
}

/** Renders a route's geometry as a polyline on the map. */
export function RouteView({ route }: RouteViewProps) {
  const positions = route.geometry.map(
    (p) => [p.latitude, p.longitude] as [number, number],
  );
  if (positions.length < 2) return null;
  return (
    <Polyline
      positions={positions}
      pathOptions={{ color: '#4f9dff', weight: 5, opacity: 0.8 }}
    >
      <Tooltip sticky>
        {`${formatDistance(route.distance_meters)} · ${formatDuration(
          route.duration_seconds,
        )}${route.is_fallback ? ' (оценка)' : ''}`}
      </Tooltip>
    </Polyline>
  );
}
