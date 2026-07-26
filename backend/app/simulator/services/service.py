"""Simulator orchestration service (Stage 17 §2, §5, §6, §7, §9).

The single entry point the API talks to. It owns the scenario store and the
session registry, builds engines from scenarios, applies trainee actions and
playback controls, and — on stop — evaluates the session and produces a report.
Everything is in-memory / file-based; the production database is never touched.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.simulator.engine.enums import SessionState, SimulationMode
from app.simulator.players.actions import ActionOutcome
from app.simulator.reports.report_builder import TrainingReport, build_report
from app.simulator.scenarios.builder import engine_from_scenario
from app.simulator.scenarios.library import built_in_scenarios
from app.simulator.scenarios.schema import Scenario
from app.simulator.scenarios.store import InMemoryScenarioStore, ScenarioStore
from app.simulator.services.session import SessionManager, TrainingSession
from app.simulator.statistics.evaluator import EvaluationResult, evaluate


class SessionAlreadyEndedError(RuntimeError):
    pass


class SimulatorService:
    def __init__(
        self,
        store: ScenarioStore | None = None,
        sessions: SessionManager | None = None,
    ) -> None:
        self._store: ScenarioStore = store or InMemoryScenarioStore(
            seed=built_in_scenarios()
        )
        self._sessions = sessions or SessionManager()

    # ----------------------------------------------------------- scenarios
    def list_scenarios(self) -> list[Scenario]:
        return self._store.list()

    def get_scenario(self, scenario_id: str) -> Scenario:
        return self._store.get(scenario_id)

    def create_scenario(self, scenario: Scenario) -> Scenario:
        return self._store.save(scenario)

    # ------------------------------------------------------------- sessions
    def start(
        self,
        scenario_id: str,
        *,
        trainee: str = "trainee",
        speed: float = 1.0,
        mode: str | None = None,
    ) -> TrainingSession:
        scenario = self._store.get(scenario_id)
        engine = engine_from_scenario(scenario, speed=speed)
        session_mode = mode or scenario.mode or SimulationMode.TRAINING.value
        # Validate the mode value early.
        SimulationMode(session_mode)
        return self._sessions.create(scenario, engine, trainee, session_mode)

    def get_session(self, session_id: str) -> TrainingSession:
        session = self._sessions.get(session_id)
        session.refresh_state()
        return session

    def _require_active(self, session_id: str) -> TrainingSession:
        session = self._sessions.get(session_id)
        if session.state in (SessionState.STOPPED, SessionState.COMPLETED):
            raise SessionAlreadyEndedError(
                f"session {session_id} has ended ({session.state.value})"
            )
        return session

    # -------------------------------------------------------------- actions
    def dispatch(
        self, session_id: str, incident_id: str, unit_ids: list[str]
    ) -> ActionOutcome:
        return self._require_active(session_id).engine.dispatch(incident_id, unit_ids)

    def resolve(self, session_id: str, incident_id: str) -> ActionOutcome:
        return self._require_active(session_id).engine.resolve(incident_id)

    # ------------------------------------------------------------- playback
    def advance(self, session_id: str, seconds: float) -> TrainingSession:
        session = self._require_active(session_id)
        session.engine.advance(seconds)
        session.refresh_state()
        return session

    def step(self, session_id: str) -> TrainingSession:
        session = self._require_active(session_id)
        session.engine.step()
        session.refresh_state()
        return session

    def pause(self, session_id: str) -> TrainingSession:
        session = self._require_active(session_id)
        session.engine.clock.pause()
        session.state = SessionState.PAUSED
        return session

    def resume(self, session_id: str) -> TrainingSession:
        session = self._require_active(session_id)
        session.engine.clock.resume()
        session.state = SessionState.RUNNING
        return session

    def set_speed(self, session_id: str, speed: float) -> TrainingSession:
        session = self._require_active(session_id)
        session.engine.clock.set_speed(speed)
        return session

    # ----------------------------------------------------------------- stop
    def stop(self, session_id: str) -> TrainingReport:
        session = self._sessions.get(session_id)
        if session.report is not None:
            return session.report
        # Let dispatched incidents that are already due settle before scoring.
        session.engine.run_to_end()
        evaluation = evaluate(session.engine, session.scenario)
        report = build_report(
            session_id=session.id,
            trainee=session.trainee,
            scenario=session.scenario,
            evaluation=evaluation,
        )
        session.report = report
        session.state = (
            SessionState.COMPLETED
            if session.engine.is_finished
            else SessionState.STOPPED
        )
        session.stopped_at = datetime.now(tz=UTC)
        return report

    # -------------------------------------------------------------- results
    def results(self, session_id: str | None = None) -> list[TrainingReport]:
        if session_id is not None:
            session = self._sessions.get(session_id)
            return [session.report] if session.report else []
        return [s.report for s in self._sessions.completed() if s.report]

    def evaluation(self, session_id: str) -> EvaluationResult:
        session = self._sessions.get(session_id)
        return evaluate(session.engine, session.scenario)

    def statistics(self) -> dict:
        reports = [s.report for s in self._sessions.completed() if s.report]
        total = len(reports)
        passed = sum(1 for r in reports if r.verdict == "passed")
        avg_score = round(sum(r.score for r in reports) / total, 1) if total else 0.0
        by_scenario: dict[str, int] = {}
        for r in reports:
            by_scenario[r.scenario_id] = by_scenario.get(r.scenario_id, 0) + 1
        return {
            "sessions_total": len(self._sessions.list()),
            "sessions_completed": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate_pct": round(100.0 * passed / total, 1) if total else 0.0,
            "avg_score": avg_score,
            "by_scenario": by_scenario,
        }
