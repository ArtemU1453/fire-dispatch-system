/**
 * Center panel — operational GIS. Uses the existing OpenLayers engine and the
 * dispatcher spatial service. Shows the incident, nearby units, straight-line
 * routes to assigned units, arrival-coverage rings, a click popup and a
 * right-click context menu. Layer visibility comes from the management store.
 */
import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import "ol/ol.css";
import OlMap from "ol/Map";
import View from "ol/View";
import TileLayer from "ol/layer/Tile";
import VectorLayer from "ol/layer/Vector";
import OSM from "ol/source/OSM";
import VectorSource from "ol/source/Vector";
import Feature from "ol/Feature";
import Point from "ol/geom/Point";
import LineString from "ol/geom/LineString";
import CircleGeom from "ol/geom/Circle";
import { Circle as CircleStyle, Fill, Stroke, Style, Text } from "ol/style";
import { fromLonLat } from "ol/proj";
import { useQuery } from "@tanstack/react-query";
import { MapService } from "@/features/dispatcher-workspace/api";
import { env } from "@/lib/env";
import { Panel } from "@/components/ui/panel";
import { useIncident, useAssignedResources } from "../hooks";
import { useManagementStore } from "../store/management.store";

function palette(token: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  const raw = getComputedStyle(document.documentElement).getPropertyValue(token).trim();
  return raw ? `hsl(${raw})` : fallback;
}

/** Coverage ring radii in metres (≈ arrival zones). */
const COVERAGE_RINGS = [1500, 3000, 5000];

function IncidentMapBase({ incidentId }: { incidentId: string }) {
  const mapElRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<OlMap | null>(null);
  const incidentSrc = useRef<VectorSource>(new VectorSource());
  const unitSrc = useRef<VectorSource>(new VectorSource());
  const routeSrc = useRef<VectorSource>(new VectorSource());
  const coverageSrc = useRef<VectorSource>(new VectorSource());

  const [menu, setMenu] = useState<{ x: number; y: number } | null>(null);

  const { data: incident } = useIncident(incidentId);
  const { resources } = useAssignedResources(incidentId);
  const layers = useManagementStore((s) => s.map.layers);

  const point = useMemo(
    () =>
      incident && incident.latitude != null && incident.longitude != null
        ? { lon: incident.longitude, lat: incident.latitude }
        : null,
    [incident],
  );

  const bbox = useMemo(
    () =>
      point
        ? {
            minLon: point.lon - 0.1,
            minLat: point.lat - 0.1,
            maxLon: point.lon + 0.1,
            maxLat: point.lat + 0.1,
          }
        : null,
    [point],
  );

  const { data: nearbyUnits = [] } = useQuery({
    queryKey: ["management", "map-units", bbox],
    queryFn: ({ signal }) => MapService.resourcesInBBox(bbox!, signal),
    enabled: Boolean(bbox) && layers.units,
    refetchInterval: env.pollResources,
  });

  // Init once.
  useEffect(() => {
    if (!mapElRef.current || mapRef.current) return;
    const incidentColor = palette("--danger", "#d7263d");
    const unitColor = palette("--success", "#2ec27e");

    const map = new OlMap({
      target: mapElRef.current,
      layers: [
        new TileLayer({ source: new OSM() }),
        new VectorLayer({
          source: coverageSrc.current,
          style: new Style({
            stroke: new Stroke({ color: "rgba(58,134,255,0.5)", width: 1 }),
            fill: new Fill({ color: "rgba(58,134,255,0.05)" }),
          }),
        }),
        new VectorLayer({
          source: routeSrc.current,
          style: new Style({
            stroke: new Stroke({ color: "#3a86ff", width: 3, lineDash: [6, 6] }),
          }),
        }),
        new VectorLayer({
          source: unitSrc.current,
          style: new Style({
            image: new CircleStyle({
              radius: 6,
              fill: new Fill({ color: unitColor }),
              stroke: new Stroke({ color: "#0e1621", width: 1.5 }),
            }),
          }),
        }),
        new VectorLayer({
          source: incidentSrc.current,
          style: new Style({
            image: new CircleStyle({
              radius: 9,
              fill: new Fill({ color: incidentColor }),
              stroke: new Stroke({ color: "#fff", width: 2 }),
            }),
            text: new Text({
              text: "ЧС",
              offsetY: -16,
              fill: new Fill({ color: incidentColor }),
              font: "600 11px Inter, sans-serif",
            }),
          }),
        }),
      ],
      view: new View({ center: fromLonLat([37.6173, 55.7558]), zoom: 12 }),
    });
    mapRef.current = map;
    map.getViewport().setAttribute("aria-label", "Оперативная карта происшествия");
    map.getViewport().addEventListener("contextmenu", (e) => {
      e.preventDefault();
      const rect = mapElRef.current!.getBoundingClientRect();
      setMenu({ x: e.clientX - rect.left, y: e.clientY - rect.top });
    });
    map.on("singleclick", () => setMenu(null));

    return () => {
      map.setTarget(undefined);
      mapRef.current = null;
    };
  }, []);

  // Incident marker + coverage + recenter.
  useEffect(() => {
    incidentSrc.current.clear();
    coverageSrc.current.clear();
    if (!point || !mapRef.current) return;
    const coord = fromLonLat([point.lon, point.lat]);
    incidentSrc.current.addFeature(new Feature({ geometry: new Point(coord) }));
    if (layers.coverage) {
      const scale = 1 / Math.cos((point.lat * Math.PI) / 180);
      for (const r of COVERAGE_RINGS) {
        coverageSrc.current.addFeature(new Feature({ geometry: new CircleGeom(coord, r * scale) }));
      }
    }
    mapRef.current.getView().animate({ center: coord, zoom: 13, duration: 400 });
  }, [point, layers.coverage]);

  // Nearby unit markers.
  useEffect(() => {
    unitSrc.current.clear();
    if (!layers.units) return;
    for (const u of nearbyUnits) {
      if (u.latitude == null || u.longitude == null) continue;
      unitSrc.current.addFeature(
        new Feature({ geometry: new Point(fromLonLat([u.longitude, u.latitude])) }),
      );
    }
  }, [nearbyUnits, layers.units]);

  // Routes from assigned units to the incident.
  useEffect(() => {
    routeSrc.current.clear();
    if (!point || !layers.routes) return;
    const byId = new Map(nearbyUnits.map((u) => [u.id, u]));
    const assignedIds = new Set(resources.map((r) => r.resourceId));
    for (const id of assignedIds) {
      const u = byId.get(id);
      if (!u || u.latitude == null || u.longitude == null) continue;
      routeSrc.current.addFeature(
        new Feature({
          geometry: new LineString([
            fromLonLat([u.longitude, u.latitude]),
            fromLonLat([point.lon, point.lat]),
          ]),
        }),
      );
    }
  }, [resources, nearbyUnits, point, layers.routes]);

  const zoomToIncident = useCallback(() => {
    if (point && mapRef.current) {
      mapRef.current.getView().animate({
        center: fromLonLat([point.lon, point.lat]),
        zoom: 15,
        duration: 400,
      });
    }
    setMenu(null);
  }, [point]);

  const toggleUnits = useManagementStore((s) => s.toggleLayer);

  return (
    <Panel
      title="Оперативная карта"
      className="h-full"
      bodyClassName="relative min-h-0 flex-1 p-0"
    >
      <div ref={mapElRef} className="absolute inset-0" />
      {menu && (
        <ul
          className="absolute z-30 min-w-[180px] rounded-md border border-border bg-panel py-1 text-xs shadow-xl"
          style={{ left: menu.x, top: menu.y }}
          role="menu"
        >
          <li>
            <button
              type="button"
              className="w-full px-3 py-1.5 text-left hover:bg-muted"
              onClick={zoomToIncident}
            >
              Приблизить к месту
            </button>
          </li>
          <li>
            <button
              type="button"
              className="w-full px-3 py-1.5 text-left hover:bg-muted"
              onClick={() => {
                toggleUnits("units");
                setMenu(null);
              }}
            >
              Показать / скрыть подразделения
            </button>
          </li>
        </ul>
      )}
    </Panel>
  );
}

export const IncidentMap = memo(IncidentMapBase);
