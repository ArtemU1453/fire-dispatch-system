"""Built-in strategic scenarios (Stage 18 §4).

Ready-to-run examples of each supported change, against the sample baseline
model. Analysts can add more via the scenario store.
"""

from __future__ import annotations

from app.digital_twin.scenarios.schema import (
    Modification,
    ModificationType,
    Scenario,
)


def _open_new_station() -> Scenario:
    return Scenario(
        id="open-south-station",
        title="Открытие подразделения на юге",
        description=(
            "Оценить эффект открытия нового подразделения в южном/западном "
            "секторе, где сейчас недостаточное покрытие."
        ),
        objectives=[
            "Повысить процент покрытия территории",
            "Сократить время прибытия в южные районы",
        ],
        modifications=[
            Modification(
                type=ModificationType.OPEN_STATION.value,
                params={"id": "S4", "name": "ПЧ-4 Юг", "x": 13, "y": 5,
                        "category": "mixed", "units": 1},
                note="Новое депо для покрытия D4/D5",
            )
        ],
    )


def _close_station() -> Scenario:
    return Scenario(
        id="close-east-station",
        title="Закрытие восточного подразделения",
        description="Оценить последствия закрытия ПЧ-3 (Восток).",
        objectives=["Оценить потерю покрытия при закрытии"],
        modifications=[
            Modification(
                type=ModificationType.CLOSE_STATION.value,
                params={"id": "S3"},
            )
        ],
    )


def _depot_repair_and_roadworks() -> Scenario:
    return Scenario(
        id="repair-and-roadworks",
        title="Ремонт депо и дорожные работы",
        description=(
            "Временный вывод ПЧ-2 на ремонт вместе с ухудшением дорожной "
            "обстановки (снижение средней скорости)."
        ),
        objectives=["Оценить устойчивость покрытия при совмещённых ограничениях"],
        modifications=[
            Modification(
                type=ModificationType.DEPOT_REPAIR.value, params={"id": "S2"}
            ),
            Modification(
                type=ModificationType.ROAD_CHANGE.value,
                params={"speed_multiplier": 0.7},
                note="Снижение скорости из-за дорожных работ",
            ),
        ],
    )


def _new_object_and_norm() -> Scenario:
    return Scenario(
        id="new-object-tighten-norm",
        title="Новый объект и ужесточение норматива",
        description=(
            "Строительство нового объекта защиты повышенного риска и ужесточение "
            "норматива времени выезда."
        ),
        objectives=[
            "Оценить нагрузку на покрытие при новом объекте",
            "Проверить достижимость более строгого норматива",
        ],
        modifications=[
            Modification(
                type=ModificationType.NEW_OBJECT.value,
                params={"id": "O5", "name": "Логистический центр", "x": 20,
                        "y": 26, "risk_class": 4},
            ),
            Modification(
                type=ModificationType.CHANGE_NORM.value,
                params={"norm_time_s": 480},
            ),
        ],
    )


def built_in_scenarios() -> list[Scenario]:
    return [
        _open_new_station(),
        _close_station(),
        _depot_repair_and_roadworks(),
        _new_object_and_norm(),
    ]
