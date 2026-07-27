/**
 * OperationalMap — the central GIS view (OpenLayers).
 *
 * Renders live unit/incident markers with clustering, a togglable layer set,
 * feature selection with a popup, zoom, and "fly to incident" support. Feature
 * data comes from `useMapData` (real API); the store drives layer visibility,
 * the current view and the fly-to request.
 */
import { memo, useCallback, useEffect, useRef, useState } from "react";
import "ol/ol.css";
import Map from "ol/Map";
import View from "ol/View";
import TileLayer from "ol/layer/Tile";
import VectorLayer from "ol/layer/Vector";
import OSM from "ol/source/OSM";
import VectorSource from "ol/source/Vector";
import Cluster from "ol/source/Cluster";
import Feature from "ol/Feature";
import Point from "ol/geom/Point";
import LineString from "ol/geom/LineString";
import Overlay from "ol/Overlay";
import { Stroke, Style } from "ol/style";
import { fromLonLat, toLonLat } from "ol/proj";
import type { FeatureLike } from "ol/Feature";
import { Panel } from "@/components/ui/panel";
import { MapLayerManager } from "./MapLayerManager";
import { MapPopup } from "./MapPopup";
import { useMapData } from "../hooks";
import { useDispatcherStore } from "../store/dispatcher.store";
import { makePointStyle } from "../utils/map-style";
import { DEFAULT_ZOOM } from "../utils/geo";
import type { MapPointFeature } from "../types";

function OperationalMapBase() {
  const mapElRef = useRef<HTMLDivElement>(null);
  const popupElRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<Map | null>(null);
  const pointSourceRef = useRef<VectorSource>(new VectorSource());
  const routeSourceRef = useRef<VectorSource>(new VectorSource());
  const overlayRef = useRef<Overlay | null>(null);
  const pointLayerRef = useRef<VectorLayer<Cluster> | null>(null);

  const [popupFeature, setPopupFeature] = useState<MapPointFeature | null>(null);

  const { features } = useMapData();
  const selectedIncidentId = useDispatcherStore((s) => s.selectedIncidentId);
  const selectIncident = useDispatcherStore((s) => s.selectIncident);
  const selectUnit = useDispatcherStore((s) => s.selectUnit);
  const setMapView = useDispatcherStore((s) => s.setMapView);
  const flyToIncidentId = useDispatcherStore((s) => s.flyToIncidentId);
  const clearFlyTo = useDispatcherStore((s) => s.clearFlyTo);
  const initialView = useDispatcherStore.getState().map;

  const selectedRef = useRef<string | null>(selectedIncidentId);
  selectedRef.current = `incident:${selectedIncidentId}`;

  // --- one-time map initialisation ----------------------------------------
  useEffect(() => {
    if (!mapElRef.current || mapRef.current) return;

    const clusterSource = new Cluster({
      distance: 42,
      source: pointSourceRef.current,
    });
    const pointLayer = new VectorLayer({
      source: clusterSource,
      style: makePointStyle(selectedRef.current),
    });
    pointLayerRef.current = pointLayer;

    const routeLayer = new VectorLayer({
      source: routeSourceRef.current,
      style: new Style({
        stroke: new Stroke({ color: "#3a86ff", width: 3, lineDash: [6, 6] }),
      }),
    });

    const overlay = new Overlay({
      element: popupElRef.current as HTMLElement,
      positioning: "bottom-center",
      offset: [0, -14],
      stopEvent: true,
    });
    overlayRef.current = overlay;

    const map = new Map({
      target: mapElRef.current,
      layers: [new TileLayer({ source: new OSM() }), routeLayer, pointLayer],
      overlays: [overlay],
      view: new View({
        center: fromLonLat([
          initialView.center.longitude,
          initialView.center.latitude,
        ]),
        zoom: initialView.zoom,
      }),
    });
    mapRef.current = map;

    map.on("moveend", () => {
      const view = map.getView();
      const center = view.getCenter();
      const zoom = view.getZoom();
      if (center && typeof zoom === "number") {
        const [lon, lat] = toLonLat(center);
        setMapView({ longitude: lon, latitude: lat }, zoom);
      }
    });

    map.on("singleclick", (evt) => {
      const hit = map.forEachFeatureAtPixel(
        evt.pixel,
        (f: FeatureLike) => f,
        { hitTolerance: 5 },
      );
      if (!hit) {
        setPopupFeature(null);
        overlay.setPosition(undefined);
        return;
      }
      const members = hit.get("features") as Feature[] | undefined;
      if (members && members.length > 1) {
        // Zoom into a cluster instead of opening a popup.
        const view = map.getView();
        view.animate({ zoom: (view.getZoom() ?? DEFAULT_ZOOM) + 2, center: evt.coordinate, duration: 250 });
        return;
      }
      const single = members && members.length ? members[0] : (hit as Feature);
      const data = single.get("data") as MapPointFeature | undefined;
      if (!data) return;
      setPopupFeature(data);
      overlay.setPosition(fromLonLat([data.longitude, data.latitude]));
      if (data.kind === "incident") selectIncident(data.id.replace("incident:", ""));
      else if (data.kind === "unit") selectUnit(data.id.replace("unit:", ""));
    });

    map.getViewport().setAttribute("tabindex", "0");
    map.getViewport().setAttribute("aria-label", "Оперативная карта");

    return () => {
      map.setTarget(undefined);
      mapRef.current = null;
    };
    // Initialise once; live updates are handled by the effects below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // --- push feature updates into the vector sources -----------------------
  useEffect(() => {
    const src = pointSourceRef.current;
    src.clear();
    const olFeatures = features.points.map((p) => {
      const f = new Feature({ geometry: new Point(fromLonLat([p.longitude, p.latitude])) });
      f.setId(p.id);
      f.set("data", p);
      return f;
    });
    src.addFeatures(olFeatures);
  }, [features.points]);

  useEffect(() => {
    const src = routeSourceRef.current;
    src.clear();
    for (const route of features.routes) {
      const line = new LineString(route.coordinates.map((c) => fromLonLat(c)));
      src.addFeature(new Feature({ geometry: line }));
    }
  }, [features.routes]);

  // --- restyle on selection change ----------------------------------------
  useEffect(() => {
    pointLayerRef.current?.setStyle(makePointStyle(`incident:${selectedIncidentId}`));
  }, [selectedIncidentId]);

  // --- fly to a requested incident ----------------------------------------
  useEffect(() => {
    if (!flyToIncidentId || !mapRef.current) return;
    const target = features.points.find((p) => p.id === `incident:${flyToIncidentId}`);
    if (!target) return; // coordinates not loaded yet; will retry when features update
    const view = mapRef.current.getView();
    view.animate({
      center: fromLonLat([target.longitude, target.latitude]),
      zoom: Math.max(view.getZoom() ?? DEFAULT_ZOOM, 14),
      duration: 400,
    });
    setPopupFeature(target);
    overlayRef.current?.setPosition(fromLonLat([target.longitude, target.latitude]));
    clearFlyTo();
  }, [flyToIncidentId, features.points, clearFlyTo]);

  const closePopup = useCallback(() => {
    setPopupFeature(null);
    overlayRef.current?.setPosition(undefined);
  }, []);

  const openIncident = useCallback(
    (id: string) => selectIncident(id),
    [selectIncident],
  );

  return (
    <Panel
      title="Оперативная карта"
      className="h-full"
      bodyClassName="relative min-h-0 flex-1 p-0"
    >
      <div ref={mapElRef} className="absolute inset-0" />
      <MapLayerManager className="absolute right-3 top-3 z-10" />
      <div ref={popupElRef} className="z-20">
        {popupFeature && (
          <MapPopup
            feature={popupFeature}
            onClose={closePopup}
            onOpenIncident={openIncident}
          />
        )}
      </div>
    </Panel>
  );
}

export const OperationalMap = memo(OperationalMapBase);
