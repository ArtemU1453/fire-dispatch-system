"""Built-in scenario library (Stage 17 §8).

A small set of ready-to-run scenarios covering the training modes. They are
authored deterministically (fixed seeds) so every trainee gets an identical,
reproducible exercise. Instructors can add more via the scenario store.
"""

from __future__ import annotations

from app.simulator.engine.enums import SimIncidentType, SimulationMode, Weather
from app.simulator.generators.incident_generator import IncidentGenConfig
from app.simulator.generators.unit_generator import (
    DisturbanceConfig,
    FleetConfig,
)
from app.simulator.scenarios.builder import scenario_from_generators
from app.simulator.scenarios.schema import (
    EvaluationCriteria,
    ExpectedResult,
    Scenario,
    ScenarioEvent,
    ScenarioUnit,
)


def _basic_training() -> Scenario:
    """A single fire — the introductory exercise."""
    return Scenario(
        id="basic-fire-01",
        title="Базовый вызов: пожар",
        description=(
            "Учебный сценарий для начинающих: один пожар, достаточные ресурсы. "
            "Цель — быстро и правильно выслать подразделение."
        ),
        mode=SimulationMode.TRAINING.value,
        objectives=[
            "Зарегистрировать происшествие",
            "Выбрать ближайшее подходящее подразделение",
            "Уложиться в норматив времени реагирования",
        ],
        seed=1,
        duration_s=600.0,
        units=[
            ScenarioUnit("U000", "АЦ-1", "fire", 2.0, 2.0, 55.0),
            ScenarioUnit("U001", "АЦ-2", "fire", 12.0, 10.0, 50.0),
            ScenarioUnit("U002", "АСМ-1", "rescue", 5.0, 5.0, 50.0),
        ],
        events=[
            ScenarioEvent(
                time_s=30.0,
                type="spawn_incident",
                id="ev-1",
                payload={
                    "id": "INC001",
                    "type": SimIncidentType.FIRE.value,
                    "x": 3.0,
                    "y": 3.0,
                    "severity": 2,
                    "required_units": 1,
                    "required_category": "fire",
                    "response_deadline_s": 120.0,
                    "label": "Пожар в жилом доме",
                },
            )
        ],
        expected=ExpectedResult(resolved_incidents=1, max_expired_incidents=0),
        criteria=EvaluationCriteria(
            max_response_time_s=120.0, min_correct_pct=100.0, max_errors=1,
            max_decision_changes=2, pass_score=70.0,
        ),
    )


def _exam_multi() -> Scenario:
    """Exam: simultaneous incidents plus breakdowns and weather."""
    scenario = scenario_from_generators(
        id="exam-multi-01",
        title="Экзамен: одновременные происшествия",
        description=(
            "Экзаменационный сценарий: несколько происшествий, поломки техники и "
            "ухудшение погоды. Оценивается приоритизация и точность решений."
        ),
        mode=SimulationMode.EXAM.value,
        seed=7,
        duration_s=1200.0,
        incidents=IncidentGenConfig(
            seed=7, count=4, horizon_s=1200.0, simultaneous=2, max_severity=3
        ),
        fleet=FleetConfig(seed=7),
        disturbances=DisturbanceConfig(
            seed=7, horizon_s=1200.0, breakdowns=1, road_closures=1,
            weather_changes=[Weather.RAIN],
        ),
        objectives=[
            "Обработать одновременные вызовы",
            "Учесть недоступность подразделений",
            "Соблюсти нормативы под нагрузкой",
        ],
    )
    scenario.criteria = EvaluationCriteria(
        max_response_time_s=150.0, min_correct_pct=80.0, max_errors=2,
        max_decision_changes=4, pass_score=75.0,
    )
    return scenario


def _mass_incident_free() -> Scenario:
    """Free modelling: a mass incident to explore resource management."""
    scenario = scenario_from_generators(
        id="mass-incident-01",
        title="Свободное моделирование: массовое происшествие",
        description=(
            "Свободный режим: крупное массовое происшествие с несколькими очагами. "
            "Без жёсткой оценки — тренировка управления ресурсами."
        ),
        mode=SimulationMode.FREE.value,
        seed=13,
        duration_s=1800.0,
        incidents=IncidentGenConfig(
            seed=13, count=3, horizon_s=1800.0, mass_incident=True, max_severity=4
        ),
        fleet=FleetConfig(seed=13),
        disturbances=DisturbanceConfig(
            seed=13, horizon_s=1800.0, breakdowns=1, unavailabilities=1,
        ),
        objectives=[
            "Распределить ограниченные ресурсы",
            "Управлять несколькими очагами одновременно",
        ],
    )
    return scenario


def built_in_scenarios() -> list[Scenario]:
    return [_basic_training(), _exam_multi(), _mass_incident_free()]
