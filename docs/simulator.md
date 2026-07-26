# Simulation & Training Platform (Stage 17)

A **fully isolated** training contour for dispatchers. It lets instructors train
staff, run exercises, replay incidents and model emergencies — and evaluates the
trainee's actions — **without ever touching the production database or the live
incident/resource data**.

> **Isolation guarantee.** The module depends on **no** SQLAlchemy session and
> adds **no** database table or migration. All simulation state is in process
> memory; scenarios are stored separately (in-memory or JSON files). Nothing
> here reads or writes real `Incident`s or units. The live system is unaffected.

## Contents
- [Architecture](#architecture)
- [Simulation engine](#simulation-engine)
- [Modes](#modes)
- [Generators](#generators)
- [Scenario format](#scenario-format)
- [Evaluation](#evaluation)
- [Instructor guide](#instructor-guide)
- [Trainee guide](#trainee-guide)
- [REST API](#rest-api)

## Architecture

```
backend/app/simulator/
  engine/        world state, clock (speed/pause/step), event application, engine
  events/        scheduled-event definitions + time-ordered queue
  generators/    incident generator + unit/environment (disturbance) generator
  scenarios/     scenario schema, JSON store, built-in library, builder
  players/       trainee actions + recording
  statistics/    evaluation (reaction time, correctness, norms, errors, accuracy)
  reports/       training-report builder
  services/      session registry + orchestration service
  schemas/       Pydantic request/response models + mapping
  api/           FastAPI routers (mounted at /training) + DI
  utils/
```

Data flow: a **Scenario** → the **builder** instantiates an **Engine** (world +
clock + event queue) → the trainee acts via the **service**/API while the
instructor controls playback → on stop the **evaluator** scores the recorded
actions and the **report builder** produces the training report.

## Simulation engine

The engine (`engine/engine.py`) drives one session deterministically:

- **World** (`engine/world.py`) — in-memory `SimUnit`s and `SimIncident`s on an
  abstract planar map (x, y in km); distance/travel-time are computed locally, so
  there is **no GIS/routing dependency**.
- **Clock** (`engine/clock.py`) — simulated time with `speed` (ускорение/
  замедление), `pause`/`resume`, `step` (пошагово) and `advance`.
- **Event queue** (`events/`) — a min-heap of `ScheduledEvent`s ordered by sim
  time; applied as the clock reaches them (spawn incident, unit breakdown/repair,
  unavailability, road closure/reopen, weather change, message).
- **Dynamics** — dispatched incidents resolve after travel + service time
  (weather slows travel); neglected pending incidents **expire** past their
  deadline; units are freed on resolution. Everything is reproducible for a
  given scenario/seed.

Trainee actions — `dispatch`, `reassign` (a re-dispatch), `resolve` — are
validated against world state and **recorded** with their sim-time for scoring.

## Modes

`engine/enums.py :: SimulationMode` — set on the scenario or overridden at start:

| Mode | Purpose |
|------|---------|
| `training` | Учебный — guided practice; hints/feedback available. |
| `exam` | Экзаменационный — graded strictly; stricter criteria. |
| `free` | Свободное моделирование — sandbox, no pass/fail pressure. |
| `replay` | Воспроизведение — replay a recorded (or real-incident-derived) timeline. |

Replaying a real incident is done by authoring a scenario from that incident's
timeline **offline** and running it in `replay` mode — the live incident is
never read or modified at runtime.

## Generators

- **Incident generator** (`generators/incident_generator.py`) — a deterministic
  (seeded) stream modelling **fires, ДТП, техногенные аварии, ложные вызовы**,
  plus **simultaneous** bursts and a **mass incident**.
- **Unit/environment generator** (`generators/unit_generator.py`) — builds a
  fleet and disturbance events: **breakdowns** (поломки), **unavailability**
  (недоступность ресурса), **road closures** (закрытие дорог) and **weather
  changes** (погодные условия) — with availability/busyness reflected in the
  engine.

Seeding makes an exercise reproducible: the same seed always yields the same
exercise.

## Scenario format

Scenarios (`scenarios/schema.py`) are serialisable (JSON) and self-describing.
Each contains (§8):

| Field | Meaning |
|-------|---------|
| `id`, `title`, `description` | identity + описание |
| `mode` | training/exam/free/replay |
| `objectives` | цели обучения |
| `seed`, `duration_s` | reproducibility + length |
| `units` | initial fleet |
| `events` | последовательность событий (timed) |
| `expected` | ожидаемый результат (resolved / max expired) |
| `criteria` | критерии оценки (norm time, min correct %, max errors, …, pass score) |

Stored via `scenarios/store.py`: `InMemoryScenarioStore` (default, seeded from
the built-in library) or `FileScenarioStore` (JSON files in a dedicated
directory — **record** = save, **replay** = load and run). A built-in library
(`scenarios/library.py`) ships three ready scenarios (basic training, exam with
simultaneous incidents + disturbances, free mass-incident).

Example (abridged):

```json
{
  "id": "basic-fire-01",
  "title": "Базовый вызов: пожар",
  "mode": "training",
  "objectives": ["Быстро выслать подразделение"],
  "units": [{"id": "U000", "name": "АЦ-1", "category": "fire", "x": 2, "y": 2}],
  "events": [{"time_s": 30, "type": "spawn_incident",
              "payload": {"id": "INC001", "type": "fire", "x": 3, "y": 3,
                          "severity": 2, "required_units": 1,
                          "required_category": "fire"}}],
  "expected": {"resolved_incidents": 1, "max_expired_incidents": 0},
  "criteria": {"max_response_time_s": 120, "pass_score": 70}
}
```

## Evaluation

`statistics/evaluator.py` computes, from the recorded actions and final world
(§7): **reaction time**, **correctness of unit selection** (right category and
enough units; false alarms should *not* be dispatched), **norm compliance**
(dispatch within the response-time norm), **error count** (rejected actions,
dispatching false alarms, expired incidents), **decision changes**
(reassignments) and **accuracy**. It aggregates a **score (0–100)** and a
**pass/fail** verdict against the scenario criteria. `reports/report_builder.py`
turns this into a structured + textual **training report** with recommendations.

## Instructor guide

1. **Choose or author a scenario** — `GET /training/scenarios`, or
   `POST /training/scenarios` with the format above (set objectives, events,
   criteria). Set the mode (`training`/`exam`/`free`/`replay`).
2. **Start a session** — `POST /training/start` with `scenario_id`, `trainee`,
   optional `speed` and `mode` override.
3. **Control playback** — `POST /training/sessions/{id}/control` with
   `pause` / `resume` / `step` / `advance` (seconds) / `set_speed`. Accelerate
   quiet periods, slow down or single-step critical moments.
4. **Observe** — `GET /training/sessions/{id}` shows sim time, incidents, unit
   statuses, weather and closed roads.
5. **Stop & review** — `POST /training/stop` returns the report (score,
   verdict, metrics, per-incident breakdown, recommendations).
6. **Track cohorts** — `GET /training/results` and `GET /training/statistics`
   (pass rate, average score, per-scenario counts).

## Trainee guide

The trainee works the incidents as they appear:

1. Watch the session view for **pending** incidents.
2. **Dispatch** the right units — `POST /training/sessions/{id}/dispatch`
   (`incident_id`, `unit_ids`). Pick units of the **required category**, enough
   of them, and the **nearest available** to meet the time norm.
3. **Do not** dispatch to **false alarms** — recognising them is part of the
   exercise.
4. **Reassign** if circumstances change (breakdown, closer unit frees up) —
   but excessive changes cost points.
5. **Resolve** handled incidents. Aim to keep reaction time within the norm and
   avoid letting incidents **expire**.

The same operational discipline as the live Dispatcher Workspace applies —
without any effect on the real database.

## REST API

Mounted under `/api/v1/training` (spec paths shown relative):

| Method & path | Purpose |
|---------------|---------|
| `GET /training/scenarios` | list scenarios (summaries) |
| `POST /training/scenarios` | create/store a scenario |
| `GET /training/scenarios/{id}` | scenario detail |
| `POST /training/start` | start a session |
| `POST /training/stop` | stop a session, return the report |
| `GET /training/results` | completed results (optionally `?session_id=`) |
| `GET /training/statistics` | aggregate training statistics |
| `GET /training/sessions/{id}` | live session state |
| `POST /training/sessions/{id}/dispatch` | dispatch units (trainee) |
| `POST /training/sessions/{id}/resolve` | resolve an incident (trainee) |
| `POST /training/sessions/{id}/control` | playback: pause/resume/step/advance/set_speed |

Errors use the standard contract: `404` unknown scenario/session, `409` action
on an ended session, `422` invalid control/scenario. Full schemas are in the
OpenAPI document at `/docs`.

## Testing

`tests/simulator/` — **database-free** unit and API tests (clock, engine
dispatch/resolve/expire, generator determinism, scenario round-trip + store,
evaluator scoring, report content, and every endpoint incl. error paths). They
run in any environment since the platform needs no PostgreSQL.
