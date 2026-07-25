# Dispatch Engine (Stage 6)

The central decision-support module (`backend/app/dispatch/`). Given an incident
(type, complexity, location and optional dispatcher constraints) it forms a
**recommended composition of forces and equipment** — primary units, reserves, a
capability-coverage report and an automatic explanation for every choice — and
persists it for later retrieval and history.

It **reuses existing services without changing them**: norms come from the
database **Rule Engine** (Stage «Rule Management»), candidates from the **Search
Engine** (Stage «Resource Search»), and locations from **GIS geocoding**.

> **Advisory only.** The engine never sends units, builds routes, computes ETA,
> reads traffic, shows a map or uses AI. It proposes the optimal option; the
> dispatcher decides.

## What changed at this stage

Dispatch norms are no longer embedded in the module. The engine obtains
**requirements, constraints, minimum / recommended composition and required
capabilities exclusively via the Rule Engine** and selects **by capability**, not
by unit name. Recommendations, their explanations and the full evaluation log are
**persisted**.

## Module layout

```
backend/app/dispatch/
├── engine.py             # DispatchEngine — the 12-step pipeline coordinator
├── config.py             # DispatchConfig (scoring weights, exclusion policy) — policy, not norms
├── eta.py                # ETAProvider interface + NullETAProvider (routing seam)
├── requirements/         # RequirementAggregator → consolidated RequirementSet
├── algorithms/
│   ├── candidate.py          # DispatchCandidate (resource + distance + caps + zones)
│   ├── scoring.py            # Scorer + RecommendationScore (configurable weights)
│   ├── capability_analyzer.py# CapabilityAnalyzer (required caps, coverage)
│   ├── priority_resolver.py  # PriorityResolver (incident priority, ranking)
│   ├── resource_selector.py  # ResourceSelector (primary composition, via strategy)
│   ├── reserve_selector.py   # ReserveSelector (reserves)
│   └── coverage_validator.py # CoverageValidator (sufficiency verdict + messages)
├── strategies/           # SelectionStrategy interface + GreedyCapabilitySelectionStrategy
├── recommendations/      # domain models + RecommendationBuilder (explanation, confidence)
├── repositories/         # CandidateRepository (Search Engine) + RecommendationRepository
├── models/               # SQLAlchemy: 7 persistence tables + enums
├── schemas/              # Pydantic request/response
├── validators/           # DispatchValidator
├── services/             # DispatchService (orchestration, persistence, history)
├── utils/                # readiness classification, domain↔ORM↔schema mapping
└── deps.py · router.py · api/dispatch.py
```

## Named components

| Component | Responsibility |
|-----------|----------------|
| `DispatchEngine` | Coordinates the whole pipeline for one incident. |
| `DispatchService` | Validates, geocodes, runs the engine, persists, serves retrieval/history. |
| `RequirementAggregator` | Consolidates the applicable rules into one `RequirementSet`. |
| `CapabilityAnalyzer` | Determines required capabilities and measures coverage. |
| `ResourceSelector` | Picks the primary composition (delegates to a `SelectionStrategy`). |
| `ReserveSelector` | Picks reserve units from the remaining candidates. |
| `CoverageValidator` | Decides sufficiency (mandatory capabilities + minimum units). |
| `PriorityResolver` | Resolves incident priority and ranks candidates. |
| `RecommendationBuilder` | Assembles the recommendation, confidence and explanations. |
| `DispatchValidator` | Validates the request (location present, self-consistent). |
| `ETAProvider` | **Interface only** — routing / ETA is a later stage. |

## Decision flow

```mermaid
flowchart TD
    A[Incident: type + complexity + address/coords + constraints] --> B{Coordinates?}
    B -- no --> G[Geocode address via GIS]
    B -- yes --> C
    G --> C[Resolve reference point]
    C --> D[Get active rules<br/>Rule Engine]
    D --> E[Consolidate requirements<br/>capabilities · min/recommended/reserve]
    E --> F[Search candidates near point<br/>Search Engine]
    F --> H[Exclude: unavailable · missing capability<br/>· out of service zone · manual — logged]
    H --> I[Score eligible<br/>distance · readiness · capability · arrival*]
    I --> J[Rank by score]
    J --> K[Determine minimum composition]
    K --> L[Pick recommended composition<br/>cover mandatory capabilities]
    L --> M[Pick reserve]
    M --> N[Validate coverage & sufficiency]
    N --> O[Build explanation + confidence]
    O --> P[Persist + return recommendation]

    style P fill:#2d6,stroke:#161
```

`*` arrival time is scored only when an `ETAProvider` returns a value — a seam for
the routing stage; today the null provider is wired in and it contributes nothing.

## Sequence

```mermaid
sequenceDiagram
    participant C as Dispatcher client
    participant API as /dispatch/recommend
    participant S as DispatchService
    participant G as GIS Geocoding
    participant RE as RuleEngine (DB)
    participant DE as DispatchEngine
    participant AG as RequirementAggregator
    participant CR as CandidateRepository
    participant SE as Search Engine
    participant RB as RecommendationBuilder
    participant RR as RecommendationRepository
    participant DB as PostgreSQL + PostGIS

    C->>API: POST {incident_type_id, complexity, address|coords, constraints}
    API->>S: recommend(request)
    S->>S: validate + ensure incident type exists
    alt address only
        S->>G: geocode(address) → point
    end
    S->>DE: recommend(incident context)
    DE->>RE: find_applicable(context)
    RE-->>DE: applicable rules (+ active versions)
    DE->>AG: aggregate → RequirementSet
    DE->>CR: fetch_candidates(point, categories, radius)
    CR->>SE: build + execute (GiST index)
    CR->>DB: batch-load capabilities + service zones
    CR-->>DE: DispatchCandidate[]
    DE->>DE: exclude · score · rank · select primary+reserve
    DE->>RB: build(coverage, sufficiency, explanations, confidence)
    RB-->>DE: Recommendation
    DE-->>S: DispatchOutcome
    S->>RR: persist (items, reasons, coverage, matches, summary, decision)
    RR->>DB: insert aggregate
    S-->>API: DispatchResponse
    API-->>C: 200 advisory recommendation
```

## Capability-driven selection

Selection is by **capability**, never by unit name. The rules state which
capabilities an incident needs (`fire_suppression`, `rescue`, `high_altitude`,
`hazmat`, `water_supply`, `lighting`, `extrication`, `evacuation`,
`radiation_control`, `gdzs`, …). Adding a new capability needs **no algorithm
change** — only a rule that requires it. `RequirementAggregator` consolidates all
applicable rules:

* **capabilities** — union, strictest `min_quantity`, mandatory wins;
* **per-category counts** — element-wise **max** of min / recommended / reserve;
* **priority** — the highest among the applicable rules.

`GreedyCapabilitySelectionStrategy` takes the top-ranked candidates up to the
recommended count, then **tops up** with any candidate that still covers an unmet
**mandatory** capability. The strategy is pluggable (`SelectionStrategy`).

## Constraints considered

Resource status · readiness · organization · service zone (by administrative
area) · priority · mandatory capabilities · recommended capabilities · minimum
composition · recommended composition · reserve. Dispatcher **manual
constraints** (allowed organizations, excluded resources, radius override,
time-of-day) are honoured and logged.

## Explanation of every decision

Each recommended unit carries an automatically generated rationale, e.g.
*«Основной: подразделение доступно, имеет требуемые возможности
(fire_suppression), на удалении 296 м, соответствует действующим правилам.»* plus
the scoring reasons. Recommendation-level notes summarise covered / missing
capabilities and sufficiency. Excluded resources are logged with a reason
(unavailable status, missing capability, out of service zone, manual exclusion).

## Persistence (ER diagram)

A **Recommendation** is the aggregate root: items (primary + reserve), their
reasons, a 1:1 summary, per-capability matches, the full resource-match log
(selected and excluded, with reasons) and a 1:1 decision (audit log).

```mermaid
erDiagram
    DISPATCH_RECOMMENDATIONS ||--o{ DISPATCH_RECOMMENDATION_ITEMS : selects
    DISPATCH_RECOMMENDATIONS ||--o{ DISPATCH_RECOMMENDATION_REASONS : explains
    DISPATCH_RECOMMENDATIONS ||--o{ DISPATCH_RESOURCE_MATCHES : logs
    DISPATCH_RECOMMENDATIONS ||--o{ DISPATCH_CAPABILITY_MATCHES : covers
    DISPATCH_RECOMMENDATIONS ||--|| DISPATCH_RECOMMENDATION_SUMMARIES : summarizes
    DISPATCH_RECOMMENDATIONS ||--|| DISPATCH_DECISIONS : audits
    DISPATCH_RECOMMENDATION_ITEMS ||--o{ DISPATCH_RECOMMENDATION_REASONS : "reasoned by"
    INCIDENT_TYPES ||--o{ DISPATCH_RECOMMENDATIONS : "typed by"
    RESOURCES ||--o{ DISPATCH_RECOMMENDATION_ITEMS : "recommended as"
    RESOURCES ||--o{ DISPATCH_RESOURCE_MATCHES : "evaluated as"

    DISPATCH_RECOMMENDATIONS {
        uuid id PK
        uuid incident_id
        uuid incident_type_id FK
        incident_complexity complexity
        float latitude
        float longitude
        rule_priority priority
        dispatch_status status
        bool sufficient
        recommendation_confidence confidence
        float confidence_score
        int total_candidates
        bool is_preview
    }
    DISPATCH_RECOMMENDATION_ITEMS {
        uuid id PK
        uuid recommendation_id FK
        uuid resource_id FK
        recommendation_role role
        float distance_meters
        float score
        varchar readiness
        int sort_order
    }
    DISPATCH_RECOMMENDATION_REASONS {
        uuid id PK
        uuid recommendation_id FK
        uuid item_id FK
        varchar text
        varchar kind
    }
    DISPATCH_RECOMMENDATION_SUMMARIES {
        uuid id PK
        uuid recommendation_id FK
        int primary_count
        int reserve_count
        int minimum_units
        int recommended_units
        int reserve_units
        jsonb required_capabilities
        jsonb covered_capabilities
        jsonb missing_capabilities
        jsonb messages
    }
    DISPATCH_RESOURCE_MATCHES {
        uuid id PK
        uuid recommendation_id FK
        uuid resource_id FK
        float distance_meters
        float score
        bool selected
        bool excluded
        dispatch_exclusion_reason exclusion_reason
        varchar detail
    }
    DISPATCH_CAPABILITY_MATCHES {
        uuid id PK
        uuid recommendation_id FK
        varchar capability_code
        int required_quantity
        int provided_quantity
        bool satisfied
        bool mandatory
    }
    DISPATCH_DECISIONS {
        uuid id PK
        uuid recommendation_id FK
        uuid incident_id
        bool decided
        dispatch_status status
        jsonb used_rule_ids
        jsonb used_rule_codes
        jsonb request_snapshot
    }
```

### PlantUML

```plantuml
@startuml AI-Dispatcher-Dispatch
hide circle
skinparam linetype ortho
skinparam classAttributeIconSize 0
' Audit columns (created_at, updated_at, is_deleted) omitted for brevity.

entity Recommendation {
  * id : uuid <<PK>>
  --
  incident_id : uuid
  * incident_type_id : uuid <<FK>>
  complexity : incident_complexity
  * latitude : float
  * longitude : float
  * priority : rule_priority
  * status : dispatch_status
  * sufficient : bool
  * confidence : recommendation_confidence
  * confidence_score : float
  * is_preview : bool
}
entity RecommendationItem {
  * id : uuid <<PK>>
  --
  * recommendation_id : uuid <<FK>>
  * resource_id : uuid <<FK>>
  * role : recommendation_role
  distance_meters : float
  score : float
  * readiness : varchar
  * sort_order : int
}
entity RecommendationReason {
  * id : uuid <<PK>>
  --
  * recommendation_id : uuid <<FK>>
  item_id : uuid <<FK>>
  * text : varchar
  kind : varchar
}
entity RecommendationSummary {
  * id : uuid <<PK>>
  --
  * recommendation_id : uuid <<FK>>
  * primary_count : int
  * reserve_count : int
  * minimum_units : int
  * recommended_units : int
  * reserve_units : int
  required_capabilities : jsonb
  covered_capabilities : jsonb
  missing_capabilities : jsonb
  messages : jsonb
}
entity ResourceMatch {
  * id : uuid <<PK>>
  --
  * recommendation_id : uuid <<FK>>
  * resource_id : uuid <<FK>>
  distance_meters : float
  score : float
  * selected : bool
  * excluded : bool
  exclusion_reason : dispatch_exclusion_reason
  detail : varchar
}
entity CapabilityMatch {
  * id : uuid <<PK>>
  --
  * recommendation_id : uuid <<FK>>
  * capability_code : varchar
  * required_quantity : int
  * provided_quantity : int
  * satisfied : bool
  * mandatory : bool
}
entity DispatchDecision {
  * id : uuid <<PK>>
  --
  * recommendation_id : uuid <<FK>>
  incident_id : uuid
  * decided : bool
  * status : dispatch_status
  used_rule_ids : jsonb
  used_rule_codes : jsonb
  request_snapshot : jsonb
}

Recommendation ||--o{ RecommendationItem
Recommendation ||--o{ RecommendationReason
Recommendation ||--o{ ResourceMatch
Recommendation ||--o{ CapabilityMatch
Recommendation ||--|| RecommendationSummary
Recommendation ||--|| DispatchDecision
RecommendationItem ||--o{ RecommendationReason
@enduml
```

The named domain entities map to these tables as: **Recommendation**,
**RecommendationItem**, **RecommendationReason**, **RecommendationSummary**,
**ResourceMatch**, **CapabilityMatch**, **DispatchDecision**. The `DispatchStatus`
enum (`recommended` / `partial` / `no_resources`) is the recommendation outcome;
`decided` is always `false` — the module advises, the dispatcher decides.

## Logging

Every run records the time of formation (`created_at`), the **rules used**
(`dispatch_decisions.used_rule_ids/codes`), the **resources used** and
**considered** with **exclusion reasons** (`dispatch_resource_matches`), the
capability coverage (`dispatch_capability_matches`), and the final recommendation
(the aggregate). The request itself is snapshotted in `request_snapshot`.

## REST API

| Method & path | Purpose |
|---------------|---------|
| `POST /api/v1/dispatch/recommend` | full recommended composition (advisory) |
| `POST /api/v1/dispatch/preview` | quick preview (no reserves) |
| `GET /api/v1/dispatch/{incident_id}` | latest recommendation for an incident |
| `GET /api/v1/dispatch/history/{incident_id}` | recommendation history for an incident |

Request (`DispatchRequest`): `incident_id`, `incident_type_id`, `complexity`,
`latitude`/`longitude` or `address`, `administrative_area_id`, `danger_level`,
`object_type`, `flags`, and `constraints` (organizations, excluded resources,
radius override, time-of-day). Response (`DispatchResponse` →
`RecommendationResponse`): status, sufficiency, confidence, required capabilities,
primary/reserve units (`RecommendationItem`), capability coverage, the
resource-match log (`ResourceMatchResponse`), a summary, messages and reasons.

## ETA seam (next stage)

`ETAProvider` is an interface only; `NullETAProvider` is wired in and returns no
estimate, so the arrival sub-score is inactive. The next stage plugs a real
routing/ETA service into this seam without changing the engine or scoring.

## Constraints (what this stage does **not** do)

No routing, no arrival-time calculation, no traffic, no map, no AI, and **no
automatic dispatch**. The module only recommends and stores; the dispatcher makes
the final decision.

## Tests

- **Unit** (`tests/dispatch/test_unit.py`, no DB): requirement aggregation,
  capability analysis, scoring, greedy selection, coverage validation, priority
  resolution, request validation, and the exclusion rules (availability,
  capability, service zone, manual).
- **Integration** (`tests/dispatch/test_engine_pg.py`, PostgreSQL): full pipeline —
  selection, mandatory-capability coverage, busy-resource exclusion with reason,
  reserves, preview, persistence and history, manual organization constraint.
- **API** (`tests/dispatch/test_api_pg.py`, PostgreSQL): recommend, preview, get,
  history and request validation over the REST surface.

PostgreSQL-backed tests skip automatically when no database is reachable.
