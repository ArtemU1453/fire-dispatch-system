# Dispatcher Guide (§12)

For dispatchers using the AI Dispatcher МЧС system at a workstation. This guide
describes the operational flow and what the system does to support decisions. It
is a support tool — **the dispatcher makes the decisions**; the system recommends
and never acts autonomously.

## The dispatch flow

1. **Call arrives** — a call is registered (telephony integration or manual
   entry). Caller/location data is captured; AI assistance can transcribe and
   extract key facts (address, incident type) to speed registration.
2. **Incident created** — the dispatcher confirms/edits the extracted details and
   opens an incident with a category and priority.
3. **Location resolved** — the address is geocoded (GIS); the map shows the
   incident and nearby resources.
4. **Recommendation** — the Dispatch Engine applies the current rules and
   proposes which units to send (candidates ranked). Routing/ETA estimates travel
   time. **This is advisory.**
5. **Decision** — the dispatcher confirms, adjusts, or overrides the
   recommendation and dispatches the chosen units.
6. **Tracking** — unit statuses and (where integrated) positions update; the
   incident progresses through its lifecycle to closure.

## What the system provides

- **Search** — quickly find resources/incidents by type, area, status, proximity.
- **Recommendations** — rule-driven unit suggestions with reasons; always
  overridable.
- **Map** — incidents and resources with location and routing context.
- **Status** — real-time incident and unit state.

## What the system does NOT do

- It does **not** dispatch automatically — every dispatch is a dispatcher action.
- It does **not** replace judgement — recommendations are inputs.
- It does **not** use AI to make the dispatch decision; AI only assists with
  call understanding.

## Good practice

- Verify the geocoded location on the map before dispatching.
- Review the recommendation's reasons; override when local knowledge warrants.
- Keep incident and unit statuses current — downstream analytics and other
  dispatchers rely on them.
- Report anything that looks wrong (bad recommendation, wrong location) to an
  administrator; changes are made via rules/settings, not ad hoc.

## Roles and visibility

Access is role-based. A dispatcher sees the operational views and their own
dispatch centre's data; management dashboards and administration are separate
roles ([admin-guide.md](admin-guide.md)). Operational analytics dashboards
(shift lead, garrison chief) present KPIs and statistics for oversight without
affecting live dispatch.
