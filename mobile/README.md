# AI Dispatcher МЧС — Mobile Platform

Two thin mobile apps over the backend BFF (`/api/v1/mobile/*`):

- **Commander** (`commander/`) — command staff (начальник смены, оперативный
  дежурный, руководитель гарнизона, РТП): dashboard, incidents, resource load,
  map, critical notifications, notes/comments.
- **Responder** (`responder/`) — field units: dispatch card, route, status
  updates, short messages.

Both depend only on the **shared SDK** (`shared/`) and contain **no business
logic** — every decision is made by the server. See
[`docs/mobile.md`](../docs/mobile.md) for architecture, offline, push, security,
API and the user guide.

## Structure

```
mobile/
  shared/
    api/            typed backend client + DTOs (the only server gateway)
    offline/        local cache + outbound queue + storage abstraction
    notifications/  provider-agnostic push client
    maps/           thin client over the existing backend GIS API
    security/       secure token store + idle auto-logout
  commander/        Commander app controller
  responder/        Responder app controller
  __tests__/        unit tests (offline, api, security, sync)
```

## Develop

```bash
npm install
npm run typecheck
npm test
```

## UI guidelines

The controllers here are UI-agnostic; the app shell (React Native / native)
renders on top of them following a **single design system**: light **and** dark
themes, large touch targets, one-handed reach (primary actions in the lower
third), and responsive phone/tablet layouts. Fast cold start (cached-first
render) and minimal network traffic (cache + batched offline sync, no polling)
are built into the SDK.
