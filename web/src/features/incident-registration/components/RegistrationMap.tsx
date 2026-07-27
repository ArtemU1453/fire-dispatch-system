/**
 * Step 3 — GIS. After an address is resolved the map centers on the incident,
 * drops a marker, shows nearby units and draws routes from the units selected
 * for dispatch to the incident point. OpenLayers; theme-aware marker colours.
 */
import { memo, useEffect, useMemo, useRef } from "react";
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
import { Circle as CircleStyle, Fill, Stroke, Style, Text } from "ol/style";
import { fromLonLat } from "ol/proj";
import { Panel } from "@/components/ui/panel";
import { Loader } from "@/components/ui/loader";
import { MapPin } from "lucide-react";
import { useNearestResources } from "../hooks";
import { useRegistrationStore } from "../store/registration.store";
import { isValidCoord } from "../utils";

const MOSCOW = { lon: 37.6173, lat: 55.7558 };

function paletteColor(token: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  const raw = getComputedStyle(document.documentElement)
    .getPropertyValue(token)
    .trim();
  return raw ? `hsl(${raw})` : fallback;
}

function RegistrationMapBase() {
  const mapElRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<OlMap | null>(null);
  const markerSrc = useRef<VectorSource>(new VectorSource());
  const unitSrc = useRef<VectorSource>(new VectorSource());
  const routeSrc = useRef<VectorSource>(new VectorSource());

  const location = useRegistrationStore((s) => s.location);
  const selectedUnits = useRegistrationStore((s) => s.selectedUnits);
  const { data: nearest = [], isFetching } = useNearestResources();

  const selectedIds = useMemo(
    () => new Set(selectedUnits.map((u) => u.resource_id)),
    [selectedUnits],
  );

  // Init once.
  useEffect(() => {
    if (!mapElRef.current || mapRef.current) return;
    const incidentColor = paletteColor("--danger", "#d7263d");
    const unitColor = paletteColor("--success", "#2ec27e");
    const selColor = paletteColor("--warning", "#ffb703");

    const markerLayer = new VectorLayer({
      source: markerSrc.current,
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
    });

    const unitLayer = new VectorLayer({
      source: unitSrc.current,
      style: (feature) => {
        const selected = feature.get("selected") as boolean;
        return new Style({
          image: new CircleStyle({
            radius: selected ? 8 : 6,
            fill: new Fill({ color: selected ? selColor : unitColor }),
            stroke: new Stroke({ color: "#0e1621", width: 1.5 }),
          }),
        });
      },
    });

    const routeLayer = new VectorLayer({
      source: routeSrc.current,
      style: new Style({
        stroke: new Stroke({ color: "#3a86ff", width: 3, lineDash: [6, 6] }),
      }),
    });

    mapRef.current = new OlMap({
      target: mapElRef.current,
      layers: [
        new TileLayer({ source: new OSM() }),
        routeLayer,
        unitLayer,
        markerLayer,
      ],
      view: new View({
        center: fromLonLat([MOSCOW.lon, MOSCOW.lat]),
        zoom: 11,
      }),
    });
    mapRef.current.getViewport().setAttribute("aria-label", "Карта места происшествия");

    return () => {
      mapRef.current?.setTarget(undefined);
      mapRef.current = null;
    };
  }, []);

  // Incident marker + recentre.
  useEffect(() => {
    markerSrc.current.clear();
    if (!location || !mapRef.current) return;
    const coord = fromLonLat([location.longitude, location.latitude]);
    markerSrc.current.addFeature(new Feature({ geometry: new Point(coord) }));
    mapRef.current.getView().animate({ center: coord, zoom: 14, duration: 400 });
  }, [location]);

  // Nearby units (highlight the selected ones).
  useEffect(() => {
    unitSrc.current.clear();
    for (const u of nearest) {
      if (!isValidCoord(u.latitude, u.longitude)) continue;
      const f = new Feature({
        geometry: new Point(fromLonLat([u.longitude as number, u.latitude])),
      });
      f.set("selected", selectedIds.has(u.id));
      unitSrc.current.addFeature(f);
    }
  }, [nearest, selectedIds]);

  // Routes from selected units to the incident.
  useEffect(() => {
    routeSrc.current.clear();
    if (!location) return;
    const byId = new Map(nearest.map((u) => [u.id, u]));
    const dest: [number, number] = [location.longitude, location.latitude];
    for (const sel of selectedUnits) {
      const u = byId.get(sel.resource_id);
      if (!u || !isValidCoord(u.latitude, u.longitude)) continue;
      const line = new LineString([
        fromLonLat([u.longitude as number, u.latitude]),
        fromLonLat(dest),
      ]);
      routeSrc.current.addFeature(new Feature({ geometry: line }));
    }
  }, [selectedUnits, nearest, location]);

  return (
    <Panel
      title="Карта места происшествия"
      className="h-full"
      bodyClassName="relative min-h-0 flex-1 p-0"
    >
      <div ref={mapElRef} className="absolute inset-0" />
      {!location && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-panel/70 text-center text-muted-foreground">
          <MapPin className="h-8 w-8" aria-hidden />
          <p className="text-sm">Выберите адрес, чтобы отобразить обстановку.</p>
        </div>
      )}
      {location && isFetching && (
        <div className="absolute left-3 top-3 z-10 rounded-md bg-panel/90 px-2 py-1">
          <Loader label="Поиск ближайших сил…" />
        </div>
      )}
    </Panel>
  );
}

export const RegistrationMap = memo(RegistrationMapBase);
