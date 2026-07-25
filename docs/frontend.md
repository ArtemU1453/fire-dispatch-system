# Dispatcher Workstation (Stage 8 · Frontend)

A React + TypeScript single-page app (`frontend/`) — the **dispatcher's
workstation**. It is a **pure client** of the existing backend: it renders data
and issues requests, and contains **no business logic** (all decisions stay on the
server). The backend is used **unchanged**.

With it a dispatcher can handle a call end-to-end: sign in → create a call card →
enter an address → see the incident on the map → get recommendations → see the
route and ETA → pick units → confirm the composition.

## Stack

React 18 · TypeScript · Vite · Material UI · TanStack React Query · React Router ·
Leaflet (react-leaflet) · Axios · Zustand.

## Architecture

```
frontend/src/
├── api/            # axios client (error normalization) + typed endpoint functions
├── types/          # TS types mirroring the backend OpenAPI contracts
├── hooks/          # React Query hooks (server state)
├── store/          # Zustand: session, incident draft/selection, notifications (UI state)
├── services/       # auth (client-side shell, RBAC-ready)
├── components/     # AddressInput, IncidentCard, RecommendationPanel, ResourceList,
│                   #   ResourceCard, MapView, RouteView, StatusBar, TopToolbar,
│                   #   NotificationPanel, SearchPanel
├── layouts/        # DispatcherLayout (top · left · center · right · bottom)
├── pages/          # LoginPage, DispatcherPage
├── features/auth/  # ProtectedRoute
├── lib/            # React Query client
├── theme/          # MUI dark control-room theme
└── utils/          # formatting helpers
```

### State: server vs UI

- **Server state → React Query.** Health, geocoding, recommendations, resource
  details, ETA and routes are fetched and cached by React Query; components read
  from the cache and never copy it into local state.
- **UI/input state → Zustand.** Only the *call being composed* (`incident` store),
  the *session* (`session` store) and *notifications* live locally. Data is never
  duplicated between the two.

## Screens

### Login (`/login`)
Username, password, shift and **role** (dispatcher / supervisor / viewer). Auth is
client-side at this stage (the backend exposes no auth API); the role feeds a
permission check (`can(...)`), so real **RBAC** slots in by replacing one service
(`services/auth.ts`) with a backend call.

### Workstation (`/`, protected)
A 1920×1080 grid:

| Region | Content |
|--------|---------|
| **Top** (`TopToolbar`) | title, clock, user + shift, connection status, global search, notifications, logout |
| **Left** (`IncidentCard`) | call number, incident type, category, address (`AddressInput`), coordinates, danger level, object type, extra info, **Get recommendations** |
| **Center** (`MapView`) | interactive Leaflet map: incident, route, units, search radius, cursor coordinates, scale |
| **Right** (`RecommendationPanel`) | status, priority, confidence, required capabilities, coverage, recommended + reserve units (distance · ETA · rationale), **Confirm composition** |
| **Bottom** (`StatusBar`) | health of Backend · GIS · Search Engine · Rule Engine · Dispatch Engine · Routing, and the time |

## Interaction with the backend

```mermaid
sequenceDiagram
    participant D as Dispatcher
    participant UI as Workstation (React)
    participant Q as React Query
    participant API as Backend API

    D->>UI: enter address
    UI->>Q: geocode(q)
    Q->>API: GET /api/v1/geocode
    API-->>UI: candidates → set incident coordinates
    D->>UI: Get recommendations
    UI->>Q: recommend(request)
    Q->>API: POST /api/v1/dispatch/recommend
    API-->>UI: recommendation (units, coverage, reasons)
    UI->>Q: unit details + ETA
    Q->>API: GET /resources/{id} · POST /routing/eta
    API-->>UI: coordinates + ETA → map markers, ETA per unit
    D->>UI: focus a unit
    UI->>Q: buildRoute(incident, unit)
    Q->>API: GET /api/v1/routing/route
    API-->>UI: route geometry → polyline on the map
    D->>UI: select units → Confirm composition
    UI-->>D: confirmed (advisory; dispatch happens outside the system)
```

### Endpoints used (all existing, unchanged)

| Feature | Endpoint |
|---------|----------|
| Address → point | `GET /api/v1/geocode` |
| Incident types (derived) | `GET /api/v1/rules`, `GET /api/v1/rules/{id}` |
| Recommendation | `POST /api/v1/dispatch/recommend`, `GET /api/v1/dispatch/{incident_id}` |
| Unit coordinates | `GET /api/v1/resources/{id}` |
| Resource search | `GET /api/v1/resources/search` |
| ETA / route | `POST /api/v1/routing/eta`, `GET /api/v1/routing/route` |
| Health | `GET /api/v1/health`, `GET /api/v1/routing/health` |

> The backend exposes no "list incident types" endpoint, so the incident-type
> picker is **derived** from the enabled dispatch rules (the dispatchable types),
> with a manual identifier entry as a fallback — **no backend change**. District
> boundaries render when a boundaries source exists; none is exposed yet.

## Map

Leaflet shows the incident (red), recommended units (blue), reserves (orange) and
the selected units (green ring); the **search radius** as a circle; the **route**
to a focused unit as a polyline (distance + ETA tooltip); the **cursor
coordinates** and a metric **scale**. Panning, zoom, object selection (popups) and
tooltips are supported.

## Error handling

`api/client.ts` normalizes every failure into an `ApiError` with a clear Russian
message by kind: network down, timeout, service unavailable (503, e.g. routing
outage), not found, validation (422), server error. Errors surface as
notifications (bell + panel) and inline states; a routing/GIS/search/recommendation
failure never breaks the rest of the workstation.

## Performance

- **Code splitting** — `react`, `mui`, `leaflet`, `query` vendor chunks; routes
  and the heavy map are **lazy-loaded** (`React.lazy` + `Suspense`).
- **Memoization** — `ResourceCard` is memoized; derived lists use `useMemo`.
- **Virtualization** — long resource-search results render via `react-window`.
- **Caching** — React Query dedupes and caches server responses (unit details and
  routes are fetched once and reused across panels).

## Tests

Vitest + React Testing Library:

- **Component** — `ResourceCard` (distance/ETA/capabilities, selection, rationale),
  `AddressInput` (geocode → sets coordinates), `StatusBar` (all engine statuses),
  formatting utils.
- **Integration** — the recommendation flow (request → render units, pre-select
  primaries), backend-failure notification, and the missing-coordinates guard —
  all against a mocked API layer.

## Running

```bash
cd frontend
npm install
npm run dev       # http://localhost:5173 (proxies /api → VITE_API_PROXY_TARGET)
npm run build     # typecheck + production bundle
npm test          # Vitest
```

Configure the API base via `VITE_API_BASE_URL` (default `/api/v1`) and the dev
proxy target via `VITE_API_PROXY_TARGET` (default `http://localhost:8000`).

## Scope

This stage delivers **only** the dispatcher workstation. No admin panel, rule
editor, analytics, AI, telephony or user management. The design leaves seams for
the next stage (telephony, automatic call-card creation, speech transcription,
multiple active incidents, multi-monitor).
