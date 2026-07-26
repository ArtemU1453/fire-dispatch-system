# Digital Twin — Strategic Analysis Platform (Stage 18)

A **digital twin** of the operational system for strategic analysis and
long-term planning. It models infrastructure-development options — opening or
closing stations, depot repairs, road changes, new objects, changed norms —
analyses **territory coverage**, **compares scenarios**, **forecasts load** and
produces **analytical materials** for leadership.

> **Isolation guarantee (§9).** The module depends on **no** database session
> and adds **no** table or migration. It works only on **copies** of the model
> (a deep copy is taken before any scenario is applied), so the baseline and the
> live dispatch system are never modified. This also makes it fully testable
> without PostgreSQL.

## Contents
- [Architecture](#architecture)
- [Digital model](#digital-model)
- [Coverage analysis](#coverage-analysis)
- [Scenario format](#scenario-format)
- [Optimization](#optimization)
- [Forecasting](#forecasting)
- [Reports](#reports)
- [REST API](#rest-api)
- [Analyst guide](#analyst-guide)

## Architecture

```
backend/app/digital_twin/
  simulation/    digital model (stations/districts/roads/water/objects) + apply
  coverage/      coverage analyzer + coverage-map grid
  scenarios/     scenario schema, JSON/in-memory store, built-in library
  optimization/  placement + scenario comparison (comparative metrics only)
  forecast/      simple statistical growth models + forecast service
  reports/       coverage/risk maps, scenario comparison, impact, justification
  planning/      DigitalTwinService facade (baseline + store + results registry)
  schemas/       Pydantic request/response + mapping
  api/           FastAPI routers (mounted at /digital-twin) + DI
  utils/
```

Flow: a **baseline** `TwinModel` (a copy) → a **scenario** is *applied* to a deep
copy → the **coverage analyzer** scores it → the **optimizer** compares options →
the **report builder** assembles maps, comparisons, impact and justification.
**Forecast** projects the drivers over a horizon.

## Digital model

`simulation/model.py :: TwinModel` holds an in-memory copy of (§2):

| Entity | Fields (key) |
|--------|--------------|
| **Station** (подразделение) | id, name, x, y, category, units, active |
| **District** (район выезда) | id, name, centroid, population, area, risk_weight, **norm_time_s** |
| **RoadNetwork** (дорожная сеть) | base speed, road (detour) factor, speed multiplier |
| **WaterSource** (водоисточник) | id, x, y, capacity |
| **ProtectedObject** (объект защиты) | id, name, x, y, risk_class (1–5) |
| **OperationalSituation** | calls/day, total population |

Coordinates are an abstract planar system (km); travel time =
`distance × road_factor / (base_speed × speed_multiplier)`. `sample_model()`
gives a small deterministic baseline used by default and in tests.

## Coverage analysis

`coverage/analyzer.py :: CoverageAnalyzer` computes (§3):

- **arrival time** to each district (nearest active station);
- **% territory covered** within the norm (uniform sampling grid) and
  **% population covered** (district-weighted);
- **risk zones** — protected objects not reached within a risk-scaled norm;
- **unreachable districts** — no station within the district norm;
- **overlap** of responsibility zones — points reachable by ≥2 stations.

`coverage_map(model)` returns a grid of cells with per-cell arrival time for
rendering a coverage map.

## Scenario format

`scenarios/schema.py` — a scenario is a serialisable list of **modifications**
(§4, §10). Applying it produces a **new** model; the baseline is never touched.

| Modification `type` | Meaning | Key `params` |
|---------------------|---------|--------------|
| `open_station` | открытие нового подразделения | id, name, x, y, category, units |
| `close_station` | закрытие подразделения | id |
| `depot_repair` | ремонт депо (временное отключение) | id |
| `road_change` | изменение дорог | speed_multiplier / road_factor / base_speed_kmh |
| `new_object` | строительство объекта защиты | id, name, x, y, risk_class |
| `change_norm` | изменение норматива выезда | norm_time_s (+ optional district_id) |

Stored via `InMemoryScenarioStore` (default, seeded from the built-in library)
or `FileScenarioStore` (JSON files). Example:

```json
{
  "id": "open-south-station",
  "title": "Открытие подразделения на юге",
  "objectives": ["Повысить покрытие территории"],
  "modifications": [
    {"type": "open_station",
     "params": {"id": "S4", "name": "ПЧ-4 Юг", "x": 13, "y": 5, "units": 1}}
  ]
}
```

## Optimization

`optimization/optimizer.py` (§5):

- **`evaluate_placements`** — scores candidate station locations by the coverage
  they would add (Δ population %, Δ territory %), ranked best-first.
- **`compare_scenarios`** — coverage metrics and deltas for a set of scenarios.

It produces **comparative metrics only** — it never applies a change or decides
automatically. The ranking is decision support for a human analyst.

## Forecasting

`forecast/` (§6) — simple, transparent statistical models (no ML): linear and
compound growth, projecting **call load**, **population**, and
**transport-accessibility** (road-speed multiplier) over a horizon. The
interface is pluggable so richer models can be added later without changing
callers. Forecasts are advisory, not decisions.

## Reports

`reports/report_builder.py` (§7) assembles:

- **coverage map** (grid cells + covered %),
- **risk map** (protected objects, arrival, high-risk-uncovered list),
- **scenario comparison** (metrics + deltas vs baseline),
- **impact assessment** per scenario (newly covered/uncovered districts, verdict),
- **justification** — a written recommendation (best/worst scenario) that
  explicitly states the decision remains with leadership.

## REST API

Mounted under `/api/v1/digital-twin` (spec paths shown relative):

| Method & path | Purpose |
|---------------|---------|
| `GET /digital-twin/scenarios` | list scenarios |
| `POST /digital-twin/scenarios` | create/store a scenario |
| `GET /digital-twin/scenarios/{id}` | scenario detail |
| `POST /digital-twin/simulate` | simulate a scenario → coverage + impact, stored |
| `GET /digital-twin/results` | stored simulation results (optionally `?result_id=`) |
| `GET /digital-twin/coverage` | baseline coverage, or `?scenario_id=` for a scenario |
| `GET /digital-twin/reports` | analytical report (optionally `?scenario_id=` repeated) |
| `POST /digital-twin/placements` | rank candidate station placements |
| `POST /digital-twin/forecast` | project load/population/accessibility |

Errors: `404` unknown scenario/result, `422` invalid scenario/modification.
Full schemas are in the OpenAPI document at `/docs`.

## Analyst guide

1. **Establish the baseline** — `GET /digital-twin/coverage` and
   `GET /digital-twin/reports` show current coverage, risk zones and unreachable
   districts.
2. **Frame a question** — author a scenario (`POST /digital-twin/scenarios`)
   with the relevant modifications (open a station, close one, change a norm…).
3. **Simulate** — `POST /digital-twin/simulate` returns the scenario's coverage
   and its **impact** (deltas, newly covered/uncovered districts, verdict).
4. **Compare options** — use `POST /digital-twin/placements` to rank candidate
   sites, or `GET /digital-twin/reports` to compare several scenarios at once.
5. **Forecast** — `POST /digital-twin/forecast` to see how load/population growth
   stresses the system over the horizon.
6. **Prepare materials** — the report's maps, comparison table, impact
   assessment and justification are the basis for a proposal to leadership.

The platform **recommends and compares** — it never changes the real system.
Every analysis runs on a copy; the baseline and production data are untouched.

## Testing

`tests/digital_twin/` — **database-free** unit, integration and scenario tests:
coverage calculation, scenario apply + **baseline-isolation**, placement/scenario
comparison, forecast math, report assembly, and every endpoint incl. error
paths. They run in any environment (no PostgreSQL required).
