# Mobile Platform — Commander & Responder (Stage 19)

Two mobile apps over a shared backend, delivered as thin clients: **Commander**
(command staff) and **Responder** (field units). All decisions and aggregation
happen on the **server** (the `app/mobile` BFF); the apps only render responses
and send actions. The apps keep working on a poor connection and synchronise
when it returns.

> **Constraint:** no business logic in the apps — the server decides everything
> (status transitions, recommendations, aggregation). The apps hold only UI
> state, a local cache and an outbound queue.

## Contents
- [Architecture](#architecture)
- [Interaction diagram](#interaction-diagram)
- [Backend BFF](#backend-bff)
- [Offline](#offline)
- [Push](#push)
- [Security](#security)
- [Maps](#maps)
- [REST API](#rest-api)
- [User guide](#user-guide)

## Architecture

```
Commander app ─┐                    ┌───────────────────────────────┐
Responder app ─┼── HTTPS REST ────▶ │  Backend BFF  app/mobile/      │
   (thin,      │   (+ push)         │   providers  (sample|adapter)  │
   shared SDK) │                    │   services   (commander/       │
               │                    │              responder/status/ │
               │                    │              offline/messages)  │
               │                    │   push       (vendor-neutral)  │
               │                    │   security   (tokens/sessions) │
               │                    └───────────────┬───────────────┘
               │                                    │ reads (production)
               │                                    ▼
               │                    existing services: incidents,
               │                    resources, routing, GIS, RBAC
```

Client SDK (`mobile/shared/`): `api` (typed backend client), `offline`
(cache + outbound queue + storage), `notifications` (push), `maps` (GIS),
`security` (token store). Apps (`mobile/commander`, `mobile/responder`) are thin
controllers composing the SDK.

The BFF reads operational data through a **provider interface**
(`app/mobile/providers`): an in-memory **sample** provider by default
(dependency-free, used by tests), swapped in production for a **real-service
adapter** over the existing incident/resource/routing services — no endpoint or
app change. The BFF adds **no database table or migration**.

## Interaction diagram

```
Responder                     BFF (server)                  Command
   │  PATCH /responder/status ───▶ validate transition            │
   │                               (state machine decides)        │
   │  ◀── 200 {status} / 409 ──────┤                              │
   │                               │ push incident_change ──────▶ │ (Commander app)
   │  (offline) enqueue op ......  │                              │
   │  reconnect: POST /sync ─────▶ apply idempotently by op_id    │
   │  ◀── results[] ───────────────┤                              │
```

## Backend BFF

`app/mobile/`:

- **providers/** — `MobileDataProvider` interface, `SampleDataProvider`
  (default) and the `RealServiceDataProvider` production seam.
- **services/** — `CommanderService` (dashboard, incidents, resources, map,
  critical notifications, notes), `ResponderService` (dispatch card, route,
  status, messages), the responder **status state machine**, the **offline
  sync** service, and the message store. The `MobilePlatform` facade wires them.
- **push/** — the vendor-neutral PushService (below).
- **security/** — the session/token store (below).

## Offline

The apps must work on an unstable connection:

- **Local cache** (`shared/offline/cache.ts`) — the last server responses are
  cached (TTL-bounded, persisted) so the app renders instantly on launch and
  shows last-known state while offline (`stale` fallback).
- **Outbound queue** (`shared/offline/queue.ts`) — status changes and messages
  are enqueued locally with a **client-generated idempotency key** (`op_id`) and
  replayed via `POST /mobile/sync` on reconnect.
- **Idempotent apply** (`app/mobile/services/offline.py`) — the server applies
  each `op_id` at most once and returns a per-op acknowledgement
  (`applied` / `duplicate` / `error`), so re-sending after a flaky connection
  never double-applies. Settled ops are dropped from the queue.

## Push

`app/mobile/push` — a **vendor-neutral** architecture (not tied to FCM/APNs/any
gateway):

- `PushProvider` interface; built-in `LogPushProvider` (records, for
  dev/tests/audit) and `NullPushProvider`. A real provider is injected by config.
- `PushService` — a device registry (per user) and event methods:
  **new incident**, **incident change**, **route change**, **new message**,
  **critical event**. On the device, `shared/notifications/push.ts` obtains a
  token via an injected `PushTransport`, registers it (`POST /mobile/devices`)
  and routes incoming messages to handlers by event type.

## Security

- **RBAC** — authorisation uses the existing Administration RBAC (roles →
  permissions); the mobile endpoints are gated by role where identity is present.
- **No plaintext passwords** — passwords are never handled on device; the app
  holds only the **session token** issued after authentication. The server-side
  `SessionStore` stores **only the SHA-256 hash** of each token, so a store leak
  exposes no usable tokens.
- **Idle auto-logout** — sessions expire after inactivity (server-side idle TTL;
  client-side `TokenStore` mirrors it and clears the token).
- **Remote termination** — an operator can revoke a single session or all of a
  user's sessions (`revoke_all_for_user`).
- **Transport** — HTTPS everywhere; sensitive values are stored encrypted on
  device (Keychain/Keystore via the `StorageAdapter`).

## Maps

The apps use the **existing** backend GIS API (`shared/maps/gis.ts`) — they do
**not** implement their own map or geocoding. The UI renders tiles with a native
map component fed by coordinates the server provides.

## REST API

Mounted under `/api/v1/mobile`:

| Method & path | Purpose |
|---------------|---------|
| `GET /mobile/commander/dashboard` | summary + active incidents + load + critical |
| `GET /mobile/commander/incidents` | active incidents (`?active_only=`) |
| `GET /mobile/commander/resources` | unit load |
| `GET /mobile/commander/map` | incidents + units with coordinates |
| `POST /mobile/commander/notes` | note / comment / confirmation |
| `GET /mobile/responder/dispatch` | dispatch card (`?unit_id=`) + current status |
| `GET /mobile/responder/route` | route to the incident (`?unit_id=`) |
| `PATCH /mobile/responder/status` | change own status (server validates) |
| `POST /mobile/responder/message` | short service message |
| `POST /mobile/devices` / `DELETE /mobile/devices/{token}` | push registration |
| `POST /mobile/sync` | replay queued offline operations (idempotent) |

Errors: `404` unknown unit/dispatch, `409` invalid status transition, `422`
invalid input/status value. Full schemas in the OpenAPI document at `/docs`.

## User guide

**Commander.** Open the app to the dashboard (loads from cache instantly, then
refreshes): operational summary, active incidents, resource load, and a
highlighted list of **critical** notifications. Tap an incident for detail and
the map. Add notes or comments; confirm decisions if your role permits. Critical
events and new incidents arrive as push notifications.

**Responder.** The app shows your **dispatch card** (address, description,
recommended composition, contact if permitted) and the **route**. Report your
status as it changes — получено → выезд → прибыл → работает → возвращается →
завершил; the server only accepts valid transitions. Send short service
messages. If you lose connection, status changes and messages are **queued** and
sent automatically when you reconnect — nothing is lost.

## Testing

- Backend: `tests/mobile/` — **database-free** unit + API tests (push, status
  FSM, offline idempotency, sessions/security, RBAC-shaped services, every
  endpoint incl. error paths).
- Client: `mobile/__tests__/` — SDK unit tests (API client + auth/401, TTL
  cache stale fallback, idle auto-logout, offline queue idempotent flush).
