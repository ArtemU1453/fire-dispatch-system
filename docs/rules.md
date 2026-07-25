# Rule Infrastructure (Stage 6)

A **universal, database-backed, versioned** store of dispatch norms
(`backend/app/rules/`). Rules live in the database — never in code — and every
algorithm obtains them through a single **Rule Engine / `RuleService`**. This
stage delivers only the *infrastructure*: it finds rules, checks their
conditions, decides which apply and returns ready-made requirements. It selects
no concrete units, builds no routes, uses no AI and makes no dispatch decisions.

> **Why in the database?** Norms change (new categories of incidents, revised
> minimum compositions, seasonal rules). Storing them as data — versioned and
> auditable — lets them evolve without redeploying code, while old versions stay
> immutable for traceability.

The next stage's dispatch algorithm will obtain **requirements, constraints,
minimum / recommended composition and required capabilities exclusively via the
Rule Engine** — it will embed no norms of its own.

## Module layout

```
backend/app/rules/
├── models/
│   ├── enums.py         # RuleStatus, RulePriority, IncidentComplexity,
│   │                    #   ConditionType, ConditionOperator, ActionType,
│   │                    #   RuleHistoryAction
│   ├── types.py         # shared native-enum objects (create_type=False)
│   └── entities.py      # 14 ORM tables (Rule, RuleVersion, …)
├── schemas/             # Pydantic Create/Update/Response per entity
│   ├── content.py       #   condition/action/requirement inputs & responses
│   ├── rule.py          #   Rule / RuleVersion / Category / RuleSet schemas
│   └── service.py       #   RequirementsResponse (ready-made composition)
├── repositories/        # RuleRepository (eager, no N+1), RuleVersionRepository
├── validators/          # RuleValidator (publish-time well-formedness)
├── executors/           # ConditionExecutor + RuleEvaluator (applicability)
├── engine.py            # RuleEngine (find → load → check → return)
├── services/
│   ├── versioning.py    #   RuleWriteService (create/version/publish/delete)
│   └── rule_service.py  #   RuleService (read facade + write delegation)
├── utils/mapping.py     # ORM → schema mapping
├── deps.py · router.py · api/rules.py   # DI + REST surface
```

Everything reuses the Stage-2 `Entity` base (UUID PK, `created_at`,
`updated_at`, `is_deleted`) and the Stage-2 `SqlAlchemyRepository`. No previous
stage's architecture is modified.

## Entities

| Table | Purpose |
|-------|---------|
| `rule_categories` | Extensible classes of rules (fires, road accidents, rescue, chemical, wildfires, false alarms, special ops, service ops). New categories are **data**, not code. |
| `rule_sets` | Named grouping of rules (e.g. a normative document / order). |
| `rules` | The logical normative. Holds identity/metadata (`code`, `name`, `is_enabled`, category, rule set). Its normative **content lives in versions**. |
| `rule_versions` | An immutable version of a rule's content. Carries `version_number`, `status`, `priority`, `is_active`, effective window, `published_at`. At most one active version per rule. |
| `rule_conditions` | Applicability conditions of a version (`condition_type`, `operator`, `field`, JSONB `value`). |
| `rule_actions` | Prescriptions of a version (`action_type`, JSONB `parameters`, `sort_order`). |
| `rule_resource_requirements` | Required composition **by category** — `min_count` / `recommended_count` / `reserve_count`, priority. Never references concrete units. |
| `rule_capability_requirements` | Required capabilities **by code** — `min_quantity`, `mandatory`. Decoupled from catalog seeding. |
| `rule_incident_types` | Junction: incident types (Stage-2 catalog) a rule applies to. |
| `rule_incident_categories` | Junction: incident complexity categories a rule applies to. |
| `rule_tags` | Free-form tags on a rule. |
| `rule_history` | Append-only audit of lifecycle events (created, version created, published, activated, updated, deleted) with JSONB `changes`. |

`RuleStatus` (`rule_status`) and `RulePriority` (`rule_priority`) are the rule
lifecycle/priority enums; `IncidentComplexity` classifies incident difficulty;
`ConditionType`/`ConditionOperator`/`ActionType`/`RuleHistoryAction` type the
content and audit rows. All are native PostgreSQL enums.

### Requirements never name units

A resource requirement describes **what capability/category is needed and how
much** (minimum, recommended, reserve, priority) — it holds no foreign keys to
resources, vehicles or organizations. Choosing concrete units is the dispatch
algorithm's job (next stage); the rules only state the norm.

## ER diagram (Mermaid)

```mermaid
erDiagram
    RULE_CATEGORIES ||--o{ RULES : classifies
    RULE_SETS ||--o{ RULES : groups
    RULES ||--o{ RULE_VERSIONS : "has (versioned)"
    RULES ||--o{ RULE_TAGS : tagged
    RULES ||--o{ RULE_INCIDENT_TYPES : "applies to"
    RULES ||--o{ RULE_INCIDENT_CATEGORIES : "scoped to"
    RULES ||--o{ RULE_HISTORY : audited
    RULE_VERSIONS ||--o{ RULE_CONDITIONS : "applicable when"
    RULE_VERSIONS ||--o{ RULE_ACTIONS : prescribes
    RULE_VERSIONS ||--o{ RULE_RESOURCE_REQUIREMENTS : requires
    RULE_VERSIONS ||--o{ RULE_CAPABILITY_REQUIREMENTS : requires
    RULE_VERSIONS ||--o{ RULE_HISTORY : references
    INCIDENT_TYPES ||--o{ RULE_INCIDENT_TYPES : "referenced by"

    RULES {
        uuid id PK
        varchar code UK
        varchar name
        bool is_enabled
        uuid category_id FK
        uuid rule_set_id FK
    }
    RULE_VERSIONS {
        uuid id PK
        uuid rule_id FK
        int version_number
        rule_status status
        rule_priority priority
        bool is_active
        timestamptz effective_from
        timestamptz effective_to
        timestamptz published_at
    }
    RULE_CONDITIONS {
        uuid id PK
        uuid rule_version_id FK
        condition_type condition_type
        condition_operator operator
        varchar field
        jsonb value
    }
    RULE_ACTIONS {
        uuid id PK
        uuid rule_version_id FK
        action_type action_type
        jsonb parameters
        int sort_order
    }
    RULE_RESOURCE_REQUIREMENTS {
        uuid id PK
        uuid rule_version_id FK
        resource_category resource_category
        varchar vehicle_type_code
        int min_count
        int recommended_count
        int reserve_count
        rule_priority priority
    }
    RULE_CAPABILITY_REQUIREMENTS {
        uuid id PK
        uuid rule_version_id FK
        varchar capability_code
        int min_quantity
        bool mandatory
    }
    RULE_HISTORY {
        uuid id PK
        uuid rule_id FK
        uuid rule_version_id FK
        rule_history_action action
        jsonb changes
        timestamptz occurred_at
    }
```

## ER diagram (PlantUML)

```plantuml
@startuml AI-Dispatcher-Rules
hide circle
skinparam linetype ortho
skinparam classAttributeIconSize 0
' Audit columns (created_at, updated_at, is_deleted) omitted for brevity.

entity RuleCategory {
  * id : uuid <<PK>>
  --
  * code : varchar <<UK>>
  * name : varchar
}
entity RuleSet {
  * id : uuid <<PK>>
  --
  * code : varchar <<UK>>
  * name : varchar
}
entity Rule {
  * id : uuid <<PK>>
  --
  * code : varchar <<UK>>
  * name : varchar
  * is_enabled : bool
  * category_id : uuid <<FK>>
  rule_set_id : uuid <<FK>>
}
entity RuleVersion {
  * id : uuid <<PK>>
  --
  * rule_id : uuid <<FK>>
  * version_number : int
  * status : rule_status
  * priority : rule_priority
  * is_active : bool
  effective_from : timestamptz
  effective_to : timestamptz
  published_at : timestamptz
}
entity RuleCondition {
  * id : uuid <<PK>>
  --
  * rule_version_id : uuid <<FK>>
  * condition_type : condition_type
  * operator : condition_operator
  field : varchar
  value : jsonb
}
entity RuleAction {
  * id : uuid <<PK>>
  --
  * rule_version_id : uuid <<FK>>
  * action_type : action_type
  parameters : jsonb
  * sort_order : int
}
entity ResourceRequirement {
  * id : uuid <<PK>>
  --
  * rule_version_id : uuid <<FK>>
  * resource_category : resource_category
  vehicle_type_code : varchar
  * min_count : int
  * recommended_count : int
  * reserve_count : int
  * priority : rule_priority
}
entity CapabilityRequirement {
  * id : uuid <<PK>>
  --
  * rule_version_id : uuid <<FK>>
  * capability_code : varchar
  * min_quantity : int
  * mandatory : bool
}
entity IncidentTypeRule {
  * id : uuid <<PK>>
  --
  * rule_id : uuid <<FK>>
  * incident_type_id : uuid <<FK>>
}
entity IncidentCategoryRule {
  * id : uuid <<PK>>
  --
  * rule_id : uuid <<FK>>
  * complexity : incident_complexity
}
entity RuleTag {
  * id : uuid <<PK>>
  --
  * rule_id : uuid <<FK>>
  * tag : varchar
}
entity RuleHistory {
  * id : uuid <<PK>>
  --
  * rule_id : uuid <<FK>>
  rule_version_id : uuid <<FK>>
  * action : rule_history_action
  changes : jsonb
  * occurred_at : timestamptz
}

RuleCategory ||--o{ Rule
RuleSet ||--o{ Rule
Rule ||--o{ RuleVersion
Rule ||--o{ RuleTag
Rule ||--o{ IncidentTypeRule
Rule ||--o{ IncidentCategoryRule
Rule ||--o{ RuleHistory
RuleVersion ||--o{ RuleCondition
RuleVersion ||--o{ RuleAction
RuleVersion ||--o{ ResourceRequirement
RuleVersion ||--o{ CapabilityRequirement
RuleVersion ||--o{ RuleHistory
@enduml
```

## The Rule Engine

`RuleEngine` (`engine.py`) is the applicability core. Given an
`EvaluationContext` (the incident's facts) it:

1. **finds** candidate rules — by incident type (`RuleRepository.by_incident_type`)
   or all enabled rules;
2. **loads** each rule's **active, published** version (`active_version`);
3. **checks** applicability — the incident-complexity scope must match, and
   `RuleEvaluator` must confirm **all** the version's conditions pass;
4. **returns** the applicable rules paired with their versions, ordered by
   priority (`critical > high > normal > low`).

It makes **no** dispatch decision and selects **no** resource.

### Condition evaluation

`ConditionExecutor` evaluates one condition against the context. Condition values
are JSONB with a small convention — `{"value": x}` (scalar), `{"values": [...]}`
(list), `{"min": a, "max": b}` (range):

| Operator | Meaning | Payload |
|----------|---------|---------|
| `eq` / `neq` | equals / not equals | `value` |
| `in` / `not_in` | membership | `values` |
| `gte` / `lte` | numeric ≥ / ≤ | `value` |
| `between` | numeric range | `min`, `max` |
| `contains` | value ∈ actual collection | `value` |
| `exists` | fact is present / non-empty | — |

Condition types map to incident facts: incident type, complexity, time of day,
administrative area, object type, priority, resource availability, capability. A
version with no conditions is unconditionally applicable.

### `RuleService`

`RuleService` is the single facade algorithms use:

| Method | Returns |
|--------|---------|
| `list_rules` / `get_rule` | rule summaries / one rule with its active version |
| `get_active_rules` | all enabled rules that have an active published version |
| `get_by_incident_type` | active rules linked to an incident type (a listing) |
| `get_by_category` | rules in a category |
| `get_versions` | every version of a rule (history preserved) |
| `get_requirements` | ready-made **minimum / recommended / reserve composition** and **required capabilities** from the active version |

`get_requirements` is the hand-off point for the next stage: it aggregates the
active version's resource requirements into per-category composition totals and
lists the mandatory capabilities — exactly what the dispatch algorithm consumes.

## REST API

| Method & path | Purpose |
|---------------|---------|
| `GET /api/v1/rules` | list rules (summaries; filter by `category_id`, `enabled_only`) |
| `GET /api/v1/rules/{id}` | one rule with its active version |
| `GET /api/v1/rules/incident/{incident_type_id}` | active rules for an incident type |
| `GET /api/v1/rules/category/{category_id}` | rules in a category |
| `GET /api/v1/rules/versions/{rule_id}` | all versions of a rule |
| `GET /api/v1/rules/{rule_id}/requirements` | ready-made requirements (active version) |
| `POST /api/v1/rules` | create a rule (+ first version, optionally published) |
| `PUT /api/v1/rules/{rule_id}` | update metadata / add a new version |
| `DELETE /api/v1/rules/{rule_id}` | soft-delete a rule |

## Rule lifecycle

```mermaid
stateDiagram-v2
    [*] --> Draft : create rule (version 1)
    Draft --> Published : publish (validate → activate)
    Published --> Archived : superseded by a newer published version
    Draft --> Deprecated : withdrawn before publishing
    Published --> Deprecated : withdrawn from use
    Archived --> [*]
    Deprecated --> [*]
    note right of Published
        Immutable. Exactly one
        active version per rule.
    end note
```

A rule's *metadata* (name, description, enabled flag, links, tags) is editable in
place. Its normative *content* (conditions, actions, requirements, priority)
lives in versions and is changed only by creating a new version.

## Versioning process

```mermaid
sequenceDiagram
    participant C as Client
    participant S as RuleWriteService
    participant V as RuleValidator
    participant DB as PostgreSQL

    C->>S: PUT /rules/{id} {new_version, publish:true}
    S->>DB: insert RuleVersion (n+1, status=draft, is_active=false)
    C-->>S: (publish requested)
    S->>V: validate_for_publish(version)
    alt invalid
        V-->>S: errors
        S-->>C: 422 ValidationError
    else valid
        S->>DB: deactivate + archive current active version (flush)
        S->>DB: set version published + active, published_at=now
        S->>DB: append rule_history (PUBLISHED, ACTIVATED)
        S-->>C: 200 RuleResponse (active_version = n+1)
    end
```

Rules of versioning enforced by `RuleWriteService`:

- **Every content change creates a new version.** Published content is never
  edited in place.
- **Published versions are immutable.** Re-publishing a published version is a
  conflict.
- **All old versions are kept.** `GET /rules/versions/{id}` returns the full
  history; superseded versions become `archived`.
- **Exactly one active version.** Guaranteed by a partial unique index
  (`uq_rule_active_version` on `rule_id WHERE is_active AND NOT is_deleted`). On
  publish, the previous active version is deactivated **and flushed first**, so
  the index never observes two active rows at once.
- **Publish is validated.** `RuleValidator` requires at least one requirement or
  action, well-formed condition payloads, no duplicate capability codes, and
  `min_count ≤ recommended_count`.
- **Everything is audited** in `rule_history`.

## Constraints (what this stage does **not** do)

- No resource **selection** — requirements describe categories/capabilities, not
  units.
- No AI, no routing, no ETA.
- Recommendations are **not executed** — the module only stores and returns
  rules.
- Previous stages' architecture is unchanged; new components reuse existing
  models, repositories and the session/DI wiring.

## Tests

- **Unit** (`tests/rules/test_unit.py`, no DB): every condition operator, version
  applicability (logical AND), and the publish-time validator.
- **Repository** (`tests/rules/test_repository_pg.py`, PostgreSQL): eager loading
  (no N+1), active-version resolution, incident-type lookup.
- **API / integration** (`tests/rules/test_api_pg.py`, PostgreSQL): create +
  publish, retrieval, versioning (new version supersedes active, old archived),
  ready-made requirements, category filter, incident-type resolution, publish
  validation, duplicate-code conflict, soft delete.

PostgreSQL-backed tests skip automatically when no database is reachable.
