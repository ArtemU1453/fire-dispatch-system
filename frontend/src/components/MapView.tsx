import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Box, Paper, Typography } from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import {
  Circle,
  MapContainer,
  Marker,
  Popup,
  TileLayer,
  useMap,
  useMapEvents,
} from 'react-leaflet';

import { useRecommendationQuery } from '../hooks/useRecommendation';
import { useUnitDetails } from '../hooks/useUnitRouting';
import { useRouteTo } from '../hooks/useUnitRouting';
import { useIncidentStore } from '../store/incident';
import { formatCoords } from '../utils/format';
import { RouteView } from './RouteView';

const DEFAULT_CENTER: [number, number] = [55.7539, 37.6208];

function markerIcon(color: string, ring = false): L.DivIcon {
  return L.divIcon({
    className: '',
    html: `<div style="width:16px;height:16px;border-radius:50%;background:${color};
      border:2px solid ${ring ? '#fff' : 'rgba(0,0,0,0.4)'};
      box-shadow:0 0 4px rgba(0,0,0,0.6)"></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
}

const INCIDENT_ICON = markerIcon('#ef5350');
const PRIMARY_ICON = markerIcon('#4f9dff');
const RESERVE_ICON = markerIcon('#ffb74d');
const SELECTED_ICON = markerIcon('#4caf50', true);

/** Adds a Leaflet scale control once. */
function ScaleControl() {
  const map = useMap();
  useEffect(() => {
    const control = L.control.scale({ imperial: false, metric: true });
    control.addTo(map);
    return () => {
      control.remove();
    };
  }, [map]);
  return null;
}

/** Reports the cursor position to the parent for the coordinate readout. */
function CursorReporter({ onMove }: { onMove: (lat: number, lon: number) => void }) {
  useMapEvents({
    mousemove: (e) => onMove(e.latlng.lat, e.latlng.lng),
  });
  return null;
}

/** Pans the map when the incident or a focused unit changes. */
function Recenter({ target }: { target: [number, number] | null }) {
  const map = useMap();
  useEffect(() => {
    if (target) map.flyTo(target, Math.max(map.getZoom(), 13), { duration: 0.5 });
  }, [map, target]);
  return null;
}

/**
 * The interactive map — incident, recommended/reserve units, the focused route,
 * the search radius, cursor coordinates and a scale. Backend supplies all data;
 * the map only renders it. (District boundaries render when a boundaries source
 * is available — none is exposed by the backend at this stage.)
 */
export function MapView() {
  const draft = useIncidentStore((s) => s.draft);
  const incidentId = useIncidentStore((s) => s.incidentId);
  const selectedIds = useIncidentStore((s) => s.selectedUnitIds);
  const searchRadius = useIncidentStore((s) => s.searchRadius);
  const mapFocus = useIncidentStore((s) => s.mapFocus);
  const [cursor, setCursor] = useState<{ lat: number; lon: number } | null>(null);

  const { data: recommendation } = useRecommendationQuery(incidentId);
  const units = useMemo(
    () => [
      ...(recommendation?.primary_units ?? []),
      ...(recommendation?.reserve_units ?? []),
    ],
    [recommendation],
  );
  const { byId: unitDetails } = useUnitDetails(units.map((u) => u.resource_id));

  const incidentPos =
    draft.latitude != null && draft.longitude != null
      ? ([draft.latitude, draft.longitude] as [number, number])
      : null;
  const focusPos = mapFocus ? ([mapFocus.lat, mapFocus.lon] as [number, number]) : null;

  const route = useRouteTo(
    incidentPos ? { lat: incidentPos[0], lon: incidentPos[1] } : null,
    focusPos ? { lat: focusPos[0], lon: focusPos[1] } : null,
  );

  return (
    <Box sx={{ position: 'relative', height: '100%', width: '100%' }}>
      <MapContainer
        center={incidentPos ?? DEFAULT_CENTER}
        zoom={12}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom
      >
        <TileLayer
          attribution="&copy; OpenStreetMap"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <ScaleControl />
        <CursorReporter onMove={(lat, lon) => setCursor({ lat, lon })} />
        <Recenter target={focusPos ?? incidentPos} />

        {incidentPos && (
          <>
            <Marker position={incidentPos} icon={INCIDENT_ICON}>
              <Popup>Место происшествия</Popup>
            </Marker>
            <Circle
              center={incidentPos}
              radius={searchRadius}
              pathOptions={{ color: '#ef5350', weight: 1, fillOpacity: 0.05 }}
            />
          </>
        )}

        {units.map((unit) => {
          const detail = unitDetails.get(unit.resource_id);
          if (detail?.latitude == null || detail?.longitude == null) return null;
          const selected = selectedIds.includes(unit.resource_id);
          const icon = selected
            ? SELECTED_ICON
            : unit.role === 'reserve'
              ? RESERVE_ICON
              : PRIMARY_ICON;
          return (
            <Marker
              key={unit.id}
              position={[detail.latitude, detail.longitude]}
              icon={icon}
            >
              <Popup>
                <strong>{unit.name}</strong>
                <br />
                {unit.code} · {unit.role === 'reserve' ? 'резерв' : 'основной'}
              </Popup>
            </Marker>
          );
        })}

        {route.data && <RouteView route={route.data} />}
      </MapContainer>

      <Paper
        elevation={3}
        sx={{
          position: 'absolute',
          bottom: 8,
          left: 8,
          px: 1,
          py: 0.25,
          zIndex: 1000,
          opacity: 0.9,
        }}
      >
        <Typography variant="caption" data-testid="cursor-coords">
          Курсор: {cursor ? formatCoords(cursor.lat, cursor.lon) : '—'}
        </Typography>
      </Paper>
    </Box>
  );
}

export default MapView;
