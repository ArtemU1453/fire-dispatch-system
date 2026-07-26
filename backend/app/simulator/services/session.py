"""Training sessions and their in-memory registry (Stage 17).

A session bundles a scenario with a running engine, the trainee identity and the
lifecycle state. Sessions live only in process memory — they are training
artefacts, kept entirely separate from the production database.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from app.simulator.engine.engine import Engine
from app.simulator.engine.enums import SessionState
from app.simulator.reports.report_builder import TrainingReport
from app.simulator.scenarios.schema import Scenario


@dataclass
class TrainingSession:
    id: str
    scenario: Scenario
    engine: Engine
    trainee: str
    mode: str
    state: SessionState = SessionState.CREATED
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    stopped_at: datetime | None = None
    report: TrainingReport | None = None

    def refresh_state(self) -> None:
        """Move to COMPLETED when the engine has nothing left to simulate."""
        if self.state == SessionState.RUNNING and self.engine.is_finished:
            self.state = SessionState.COMPLETED


class SessionNotFoundError(KeyError):
    def __init__(self, session_id: str) -> None:
        super().__init__(session_id)
        self.session_id = session_id


class SessionManager:
    """Thread-safe in-memory registry of training sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, TrainingSession] = {}
        self._lock = threading.Lock()

    def create(
        self, scenario: Scenario, engine: Engine, trainee: str, mode: str
    ) -> TrainingSession:
        session = TrainingSession(
            id=uuid4().hex,
            scenario=scenario,
            engine=engine,
            trainee=trainee,
            mode=mode,
            state=SessionState.RUNNING,
        )
        with self._lock:
            self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> TrainingSession:
        with self._lock:
            try:
                return self._sessions[session_id]
            except KeyError as exc:
                raise SessionNotFoundError(session_id) from exc

    def list(self) -> list[TrainingSession]:
        with self._lock:
            return list(self._sessions.values())

    def completed(self) -> list[TrainingSession]:
        with self._lock:
            return [
                s
                for s in self._sessions.values()
                if s.report is not None
            ]
