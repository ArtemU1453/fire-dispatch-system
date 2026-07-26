"""Training report builder (Stage 17 §7, §10).

Turns an :class:`EvaluationResult` plus scenario/session metadata into a
structured training report (and a human-readable summary) for the instructor and
the trainee.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.simulator.scenarios.schema import Scenario
from app.simulator.statistics.evaluator import EvaluationResult


@dataclass
class TrainingReport:
    session_id: str
    scenario_id: str
    scenario_title: str
    mode: str
    trainee: str
    verdict: str                       # "passed" | "failed"
    score: float
    metrics: dict[str, Any] = field(default_factory=dict)
    objectives: list[str] = field(default_factory=list)
    per_incident: list[dict] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__

    def to_text(self) -> str:
        lines = [
            f"Отчёт по обучению — сессия {self.session_id}",
            f"Сценарий: {self.scenario_title} ({self.scenario_id}), режим: {self.mode}",
            f"Обучаемый: {self.trainee}",
            f"Результат: {'ЗАЧЁТ' if self.verdict == 'passed' else 'НЕ ЗАЧТЕНО'} "
            f"(оценка {self.score}/100)",
            "",
            "Показатели:",
        ]
        labels = {
            "avg_reaction_time_s": "Среднее время реакции, с",
            "norm_compliance_pct": "Соответствие нормативу, %",
            "correct_pct": "Правильность решений, %",
            "accuracy_pct": "Точность, %",
            "error_count": "Количество ошибок",
            "decision_changes": "Изменений решения",
            "resolved_incidents": "Обработано происшествий",
            "expired_incidents": "Просрочено происшествий",
        }
        for key, label in labels.items():
            if key in self.metrics:
                lines.append(f"  - {label}: {self.metrics[key]}")
        if self.recommendations:
            lines.append("")
            lines.append("Рекомендации:")
            lines.extend(f"  • {r}" for r in self.recommendations)
        return "\n".join(lines)


def _recommendations(ev: EvaluationResult, scenario: Scenario) -> list[str]:
    recs: list[str] = []
    c = scenario.criteria
    if ev.norm_compliance_pct < c.min_correct_pct:
        recs.append(
            "Сократить время реагирования: выбирать ближайшие свободные подразделения."
        )
    if ev.error_count > c.max_errors:
        recs.append(
            "Снизить число ошибок: проверять статус и категорию подразделения "
            "перед высылкой; не реагировать высылкой на ложные вызовы."
        )
    if ev.decision_changes > c.max_decision_changes:
        recs.append(
            "Меньше менять решение: анализировать обстановку до назначения."
        )
    if ev.correct_pct < c.min_correct_pct:
        recs.append(
            "Повысить правильность: направлять достаточное число подразделений "
            "нужной категории."
        )
    if not recs:
        recs.append("Действия соответствуют нормативам — хороший результат.")
    return recs


def build_report(
    *,
    session_id: str,
    trainee: str,
    scenario: Scenario,
    evaluation: EvaluationResult,
) -> TrainingReport:
    metrics = {
        "avg_reaction_time_s": evaluation.avg_reaction_time_s,
        "norm_compliance_pct": evaluation.norm_compliance_pct,
        "correct_pct": evaluation.correct_pct,
        "accuracy_pct": evaluation.accuracy_pct,
        "error_count": evaluation.error_count,
        "decision_changes": evaluation.decision_changes,
        "resolved_incidents": evaluation.resolved_incidents,
        "expired_incidents": evaluation.expired_incidents,
        "total_incidents": evaluation.total_incidents,
    }
    return TrainingReport(
        session_id=session_id,
        scenario_id=scenario.id,
        scenario_title=scenario.title,
        mode=scenario.mode,
        trainee=trainee,
        verdict="passed" if evaluation.passed else "failed",
        score=evaluation.score,
        metrics=metrics,
        objectives=list(scenario.objectives),
        per_incident=[ie.__dict__ for ie in evaluation.per_incident],
        recommendations=_recommendations(evaluation, scenario),
    )
