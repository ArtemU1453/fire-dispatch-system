# AI Dispatcher МЧС — Enterprise Frontend (Этап 1: Application Shell)

Foundation of the AI Dispatcher МЧС web client: authentication, the Enterprise
layout, navigation, routing, the API layer, global state, the base component
library, theming and the test infrastructure. Built to be extended by the next
frontend stages without architectural change.

> This is the new Enterprise shell (React 19 + Tailwind + shadcn/ui). It is a
> separate app from the earlier `../frontend/` MUI prototype.

## Stack

React 19 · TypeScript · Vite 6 · React Router v7 · TanStack Query v5 · Zustand v5
· React Hook Form + Zod · Axios · TailwindCSS 3 · shadcn/ui (Radix) · Lucide ·
react-error-boundary · OpenLayers (installed; map arrives next stage). Tests:
Vitest + React Testing Library + Playwright.

## Getting started

```bash
cd web
cp .env.example .env      # configure VITE_API_BASE_URL etc. (no URLs in code)
npm install
npm run dev               # http://localhost:5173 (proxies /api → backend)
npm run build             # type-check + production build
npm test                  # unit tests (Vitest + RTL)
npm run e2e               # end-to-end (Playwright; needs the dev server)
```

## Architecture (Feature-Sliced Design)

```
src/
  app/           application root + router composition
  layouts/       EnterpriseLayout (Header / Sidebar / Content / Footer)
  pages/         route screens (login, dashboard, incidents, …, 404, error)
  features/      feature slices (auth: login form + schema)
  components/
    ui/          base component library (shadcn-style, Radix + cva)
    layout/      Header, Sidebar, Footer, NotificationPanel, nav
  hooks/         useAuth, useClock
  services / api api client (Axios + interceptors + refresh + retry), auth API
  store/         Zustand stores (auth, user, notification, settings)
  routes/        paths, ProtectedRoute
  providers/     AppProviders (Query + ErrorBoundary + Toaster), AuthProvider
  types/         shared TypeScript types
  lib/ utils/    cn(), env, formatting
  styles/        Tailwind + CSS-variable theme tokens
```

### Layout & theming

All layout metrics (header height, sidebar width, etc.) and colors are defined
as **CSS variables** in `styles/index.css`. The app ships a **dark** enterprise
theme; a **light** theme is fully defined and switchable (Settings → Оформление)
for the future. Colors follow the МЧС palette mapped to shadcn-style HSL tokens.

### Authentication (JWT)

- `AuthProvider` handles idle auto-logout; `useAuth` exposes `login`/`logout`.
- The Axios client attaches the access token, transparently **refreshes** on
  `401` (single-flight queue) and retries the original request, performs a
  **retry policy** for network/5xx GETs, and normalizes errors. On refresh
  failure it clears the session (reactive stores redirect via `ProtectedRoute`).
- Tokens live in the `auth` store (persisted); the profile/permissions live in
  the `user` store. Routing is guarded by `ProtectedRoute` (RBAC-ready via
  `permission`).

### State

Four Zustand stores: **auth** (tokens), **user** (profile + `hasPermission`/
`hasRole`), **notification** (panel + items), **settings** (theme + sidebar,
persisted).

### Error handling

A global `ErrorBoundary` (react-error-boundary) with a themed fallback, plus
dedicated `404` and error screens; network/API errors are normalized to a
consistent shape.

## Base components

`Button, Input, Label, Checkbox, Select, Card, Panel, Badge, Table, Tabs,
Dialog (Modal), Toast/Toaster, Loader, Skeleton` — all implemented (no stubs),
theme-aware, keyboard-accessible.

## Configuration

Everything is read from `.env` (`VITE_*`) — **no URLs are hard-coded**. See
`.env.example`.

## Security

Idle auto-logout, `401` refresh + `403` handling, RBAC-ready routing, and
CSRF-ready headers on the Axios client.
