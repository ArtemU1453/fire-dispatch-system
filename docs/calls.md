# Call Management (Stage 11)

This module (`backend/app/calls/`) is the **reception, registration and
processing of emergency calls**. Every incoming call becomes its own entity and
is linked to one or more **incident** cards (Stage 9). Around the call it models
the dispatch **queue** (multi-workstation), an append-only **history**,
**participants**, **recordings** and **transcripts** (architecture only — no
audio / ASR yet), the **incident links** and free-form **metadata**.

This stage delivers the **infrastructure**. Real telephony, call recording and
speech recognition are deliberately **not** implemented; they plug into the seams
described below without changing the module. The Dispatch Engine and Incident
Management modules are **not modified** — only Incident Management's public
service is consumed.

## Module layout

```
backend/app/calls/
├── models/          # SQLAlchemy: 8 tables + enums + shared enum types
├── validators/      # the call lifecycle state machine (allowed transitions)
├── providers/       # CallProvider interface + MockCallProvider (telephony seam)
├── queue/           # CallQueueManager (priority queue, multi-workstation)
├── history/         # CallHistoryRecorder (append-only audit)
├── repositories/    # CallRepository (eager reads, queue & history queries)
├── services/        # CallService + CallIncidentLinker (incident create/link)
├── schemas/         # Pydantic Create / Update / Response
├── utils/           # Actor, ORM → schema mapping
└── deps.py · router.py · api/calls.py
```

## Entities

| Table | Purpose |
|-------|---------|
| `calls` | The call card: number, external (provider) id, direction, **type**, **source**, **status**, **priority**, caller / callee number, dispatcher, linked incident, and the reception / answer / end timestamps + wait / talk durations. |
| `call_queue` | The call's position in the dispatch queue: priority, status, arrival time, assigned dispatcher / **workstation**, wait time. |
| `call_history` | **Append-only** history: status changes, queueing, dispatcher assignment, incident creation / linking, provider actions — with actor, source, old → new status and the related incident. |
| `call_participants` | Parties on the call (caller, dispatcher, transfer target, …). |
| `call_recordings` | Recording **metadata** only (external ref, format, duration, storage location, processing status) — no audio. |
| `call_transcripts` | Transcript **placeholder** (source text, temporal segments as JSONB, language, processing status) — no ASR. |
| `call_incident_links` | Links a call to incident cards (`created` vs `linked`, primary flag). |
| `call_metadata` | Free-form key/value metadata (extension seam). |

Enums (native PostgreSQL): `call_status`, `call_priority`, `call_type`,
`call_source`, `call_direction`, `call_event_type`, `call_queue_status`,
`call_participant_role`, `call_recording_status`, `call_transcript_status`,
`call_link_type`.

The domain concepts **CallStatus / CallType / CallSource** are modelled as native
enums (the project convention for lifecycle / classification values), consistent
with the incident module.

## Call lifecycle

Statuses: **Новый** (`new`) → **Ожидает ответа** (`ringing`) → **Принят**
(`accepted`) → **В обработке** (`in_progress`) → **Связан с Incident** (`linked`)
→ **Завершён** (`completed`); **Отменён** (`cancelled`) before completion and
**Ошибка** (`error`) from any active state.

Transitions are enforced by a finite state machine
(`validators/state_machine.py`); **invalid transitions are rejected** (HTTP 422).

```mermaid
stateDiagram-v2
    [*] --> new
    new --> ringing
    new --> accepted
    new --> linked : создать/привязать Incident
    ringing --> accepted
    ringing --> linked
    accepted --> in_progress
    accepted --> linked
    in_progress --> linked
    linked --> in_progress
    linked --> completed
    in_progress --> completed
    accepted --> completed
    new --> cancelled
    ringing --> cancelled
    accepted --> cancelled
    in_progress --> cancelled
    linked --> cancelled
    new --> error
    accepted --> error
    in_progress --> error
    error --> in_progress
    error --> completed
    completed --> [*]
    cancelled --> [*]
```

Each status change records a `call_history` entry (event, old → new, actor,
source, related incident) and sets the relevant timestamp: `answered_at` (with
the computed `wait_seconds`) on first answer, `ended_at` (with `talk_seconds`) on
completion / cancellation.

## Call queue

A new call enters the queue immediately. The queue supports **priority**, arrival
time (`enqueued_at`), the assigned dispatcher and **workstation**, and a status —
so several dispatcher workstations can pull from one shared queue. Wait time is
computed from the arrival time. The listing is ordered most-urgent first
(priority rank, then arrival time).

```mermaid
flowchart LR
    NEW[Новый вызов] --> ENQ[enqueue → waiting]
    ENQ --> ASSIGN[assign → assigned<br/>диспетчер + рабочее место]
    ASSIGN --> INPROG[in_progress]
    INPROG --> DONE[done<br/>убран из очереди]
    ENQ -. не дождались .-> ABANDONED[abandoned]
```

Queue statuses: `waiting` → `assigned` → `in_progress` → `done`; `abandoned` when
a call is closed before it was ever answered.

## Integration with Incident Management

Every call either **creates a new incident card** or is **attached to an existing
one**. That selection logic is isolated in a dedicated service —
`CallIncidentLinker` — which reuses the Stage-9 `IncidentService` **unchanged**:

```mermaid
flowchart LR
    CALL[Call] --> LINKER[CallIncidentLinker]
    LINKER -->|create| INC_NEW[IncidentService.create → new Incident]
    LINKER -->|link| INC_OLD[existing Incident]
    INC_NEW --> LINK[(call_incident_links · created)]
    INC_OLD --> LINK2[(call_incident_links · linked)]
    LINK --> CALL
    LINK2 --> CALL
```

`POST /calls/{id}/incident` takes **either** an `incident_id` (link existing)
**or** `create=true` (create new from the call's caller / address data); providing
both or neither is rejected. On success the call moves to `linked`, `incident_id`
is set to the primary incident, and a `call_incident_links` row records the link
type.

## CallProvider interface (telephony seam)

Telephony is **not** connected at this stage. All interaction with a phone
platform goes through the abstract `CallProvider`
(`providers/base.py`), so a real backend (Asterisk, FreeSWITCH, SIP, WebRTC, …)
can be plugged in later **without changing** the call service:

```python
class CallProvider(ABC):
    async def receive_call(...) -> ProviderCall: ...
    async def answer_call(external_id) -> ProviderCall: ...
    async def end_call(external_id) -> ProviderCall: ...
    async def hold_call(external_id) -> ProviderCall: ...
    async def transfer_call(external_id, *, destination) -> ProviderCall: ...
    async def health_check() -> ProviderHealth: ...
```

The only implementation now is **`MockCallProvider`** — a deterministic in-memory
provider that fully implements the interface (tracked calls, simulated state
transitions). It is wired as a process-wide singleton in `deps.py`, so a call's
provider handle survives across requests. `GET /calls/provider/health` reports
its status.

## Recording & transcription (architecture only)

`call_recordings` stores a recording's **id / external ref, duration, format,
storage location and processing status** — no audio is captured.
`call_transcripts` stores the **source text, temporal segments (JSONB), language
and processing status** — no speech recognition runs. Both exist so a real
recording backend and an ASR engine (and later an AI analyser) can populate them
without schema changes.

## ER diagram (Mermaid)

```mermaid
erDiagram
    CALLS ||--o| CALL_QUEUE : "queued as"
    CALLS ||--o{ CALL_HISTORY : audits
    CALLS ||--o{ CALL_PARTICIPANTS : has
    CALLS ||--o{ CALL_RECORDINGS : records
    CALLS ||--o{ CALL_TRANSCRIPTS : transcribes
    CALLS ||--o{ CALL_INCIDENT_LINKS : links
    CALLS ||--o{ CALL_METADATA : annotates
    INCIDENTS ||--o{ CALL_INCIDENT_LINKS : "linked from"
    INCIDENTS ||--o| CALLS : "primary incident"

    CALLS {
        uuid id PK
        varchar number UK
        varchar external_id
        call_direction direction
        call_type call_type
        call_source source
        call_status status
        call_priority priority
        varchar caller_number
        uuid dispatcher_user_id FK
        uuid incident_id FK
        timestamptz received_at
        timestamptz answered_at
        timestamptz ended_at
        int wait_seconds
        int talk_seconds
    }
    CALL_QUEUE {
        uuid id PK
        uuid call_id FK
        call_priority priority
        call_queue_status status
        timestamptz enqueued_at
        timestamptz assigned_at
        uuid dispatcher_user_id FK
        varchar workstation
    }
    CALL_HISTORY {
        uuid id PK
        uuid call_id FK
        call_event_type event_type
        call_status from_status
        call_status to_status
        varchar source
        uuid incident_id FK
        timestamptz occurred_at
    }
    CALL_INCIDENT_LINKS {
        uuid id PK
        uuid call_id FK
        uuid incident_id FK
        call_link_type link_type
        bool is_primary
    }
    CALL_RECORDINGS {
        uuid id PK
        uuid call_id FK
        varchar external_ref
        int duration_seconds
        varchar storage_ref
        call_recording_status status
    }
    CALL_TRANSCRIPTS {
        uuid id PK
        uuid call_id FK
        varchar language
        text text_content
        jsonb segments
        call_transcript_status status
    }
```

## ER diagram (PlantUML)

```plantuml
@startuml AI-Dispatcher-Calls
hide circle
skinparam linetype ortho
skinparam classAttributeIconSize 0
' Audit columns (created_at, updated_at, is_deleted) omitted for brevity.
' incidents / organizations / users are existing entities — referenced, not modified.

entity Call {
  * id : uuid <<PK>>
  --
  * number : varchar <<UK>>
  external_id : varchar
  * direction : call_direction
  * call_type : call_type
  * source : call_source
  * status : call_status
  * priority : call_priority
  caller_number : varchar
  dispatcher_user_id : uuid <<FK>>
  incident_id : uuid <<FK>>
  * received_at : timestamptz
  answered_at : timestamptz
  ended_at : timestamptz
  wait_seconds : int
  talk_seconds : int
}
entity CallQueueEntry {
  * id : uuid <<PK>>
  --
  * call_id : uuid <<FK>> <<UK>>
  * priority : call_priority
  * status : call_queue_status
  * enqueued_at : timestamptz
  assigned_at : timestamptz
  dispatcher_user_id : uuid <<FK>>
  workstation : varchar
}
entity CallHistory {
  * id : uuid <<PK>>
  --
  * call_id : uuid <<FK>>
  * event_type : call_event_type
  from_status : call_status
  to_status : call_status
  * source : varchar
  incident_id : uuid <<FK>>
  * occurred_at : timestamptz
}
entity CallParticipant {
  * id : uuid <<PK>>
  --
  * call_id : uuid <<FK>>
  * role : call_participant_role
  name : varchar
  phone_number : varchar
  organization_id : uuid <<FK>>
}
entity CallRecording {
  * id : uuid <<PK>>
  --
  * call_id : uuid <<FK>>
  external_ref : varchar
  audio_format : varchar
  duration_seconds : int
  storage_ref : varchar
  * status : call_recording_status
}
entity CallTranscript {
  * id : uuid <<PK>>
  --
  * call_id : uuid <<FK>>
  language : varchar
  text_content : text
  segments : jsonb
  * status : call_transcript_status
}
entity CallIncidentLink {
  * id : uuid <<PK>>
  --
  * call_id : uuid <<FK>>
  * incident_id : uuid <<FK>>
  * link_type : call_link_type
  * is_primary : bool
}
entity CallMetadata {
  * id : uuid <<PK>>
  --
  * call_id : uuid <<FK>>
  * key : varchar
  value : varchar
}

Call ||--o| CallQueueEntry
Call ||--o{ CallHistory
Call ||--o{ CallParticipant
Call ||--o{ CallRecording
Call ||--o{ CallTranscript
Call ||--o{ CallIncidentLink
Call ||--o{ CallMetadata
@enduml
```

## REST API

| Method & path | Purpose |
|---------------|---------|
| `POST /api/v1/calls` | register a call (optionally register it with the provider) |
| `GET /api/v1/calls` | list calls (summaries; `active` filter) |
| `GET /api/v1/calls/{id}` | full call card |
| `PATCH /api/v1/calls/{id}/status` | change status (state machine) |
| `POST /api/v1/calls/{id}/incident` | create or link an incident *(integration)* |
| `GET /api/v1/calls/queue` | the dispatch queue (most urgent first) |
| `GET /api/v1/calls/history` | call history (global or `?call_id=`) |
| `POST /api/v1/calls/{id}/assign` | assign a dispatcher / workstation |
| `POST /api/v1/calls/{id}/answer` | answer (via the provider) |
| `POST /api/v1/calls/{id}/hold` · `/transfer` · `/end` | telephony actions |
| `GET /api/v1/calls/provider/health` | telephony provider health |

The literal `/calls/queue`, `/calls/history` and `/calls/provider/health` routes
are registered **before** the dynamic `/calls/{call_id}` so they are not shadowed.

Pydantic schemas: `CallCreate`, `CallUpdate`, `CallResponse`,
`CallSummaryResponse`, `CallQueueResponse`, `CallHistoryResponse`,
`CallTranscriptResponse` (plus nested participant / recording / link responses and
the request models for assignment, incident linking and transfer).

## Logging

Every meaningful change is captured in `call_history`: the reception time, the
answer time, the end time, the assigned dispatcher, the created / linked incident
and all status changes — with the actor and source, and **never deleted**.

## Constraints

Per the stage brief this module does **not**: connect real IP telephony,
implement call recording, implement speech recognition, or use AI. It does not
modify the Dispatch Engine or Incident Management. It leaves seams for the next
(AI) stage — real telephony (SIP / Asterisk / FreeSWITCH), recording,
transcription, caller-number lookup, automatic address detection and AI
conversation analysis — to plug in without architectural change.

## Tests

- **Unit** (`tests/calls/test_unit.py`): the lifecycle happy path, rejected
  invalid transitions, reversible `linked`, recoverable `error`, terminal states,
  and the full `MockCallProvider` flow (receive → answer → hold → transfer → end,
  health, unknown-call error).
- **Integration** (`tests/calls/test_service_pg.py`, PostgreSQL): call creation +
  queueing + history, status progression with timestamps, invalid / duplicate
  transition handling, dispatcher assignment, **incident create** and **link
  existing** (with the exactly-one-choice rule), priority queue ordering, the
  provider answer/end flow, recording / transcript registration, append-only
  history.
- **API** (`tests/calls/test_api_pg.py`, PostgreSQL): create / get / list, status
  change (valid + 422), incident create / link / ambiguous-choice, queue,
  dispatcher assignment, history, provider health and the answer/end flow.

PostgreSQL-backed tests skip automatically when no database is reachable.
