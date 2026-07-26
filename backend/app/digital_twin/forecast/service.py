"""Forecast service (Stage 18 §6).

Projects the operational drivers over a horizon using simple statistical models
and reports the implied strain on the system. It reads a **copy** of the model
and changes nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.digital_twin.forecast.models import (
    CompoundGrowthModel,
    LinearGrowthModel,
    ProjectionPoint,
)
from app.digital_twin.simulation.model import TwinModel


@dataclass
class ForecastConfig:
    horizon_years: int = 5
    call_growth_rate: float = 0.04            # рост числа вызовов / нагрузки
    population_growth_rate: float = 0.02      # изменение плотности населения
    accessibility_change_rate: float = 0.0    # +/- транспортная доступность
    compound: bool = False                    # compound vs linear growth


@dataclass
class ForecastResult:
    horizon_years: int
    calls_per_day: list[ProjectionPoint] = field(default_factory=list)
    population_total: list[ProjectionPoint] = field(default_factory=list)
    # Accessibility expressed as a road-speed multiplier over time.
    accessibility_multiplier: list[ProjectionPoint] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "horizon_years": self.horizon_years,
            "calls_per_day": [p.__dict__ for p in self.calls_per_day],
            "population_total": [p.__dict__ for p in self.population_total],
            "accessibility_multiplier": [
                p.__dict__ for p in self.accessibility_multiplier
            ],
            "notes": self.notes,
        }


class ForecastService:
    def forecast(self, model: TwinModel, config: ForecastConfig) -> ForecastResult:
        years = max(0, config.horizon_years)
        call_model = self._model(config.call_growth_rate, config.compound)
        pop_model = self._model(config.population_growth_rate, config.compound)
        acc_model = LinearGrowthModel(config.accessibility_change_rate)

        result = ForecastResult(horizon_years=years)
        result.calls_per_day = call_model.project(model.situation.calls_per_day, years)
        result.population_total = pop_model.project(
            float(model.situation.population_total or 0), years
        )
        result.accessibility_multiplier = acc_model.project(
            model.road.speed_multiplier, years
        )

        end_calls = result.calls_per_day[-1].value if result.calls_per_day else 0
        start_calls = result.calls_per_day[0].value if result.calls_per_day else 0
        if start_calls:
            growth_pct = round(100.0 * (end_calls - start_calls) / start_calls, 1)
            result.notes.append(
                f"Нагрузка по вызовам за {years} лет вырастет на ~{growth_pct}%."
            )
        if config.accessibility_change_rate < 0:
            result.notes.append(
                "Снижение транспортной доступности ухудшит время прибытия — "
                "рекомендуется пересчёт покрытия при сниженной скорости."
            )
        result.notes.append(
            "Прогноз построен на простых статистических моделях (без ML) и служит "
            "ориентиром для планирования, а не автоматическим решением."
        )
        return result

    @staticmethod
    def _model(rate: float, compound: bool):
        return CompoundGrowthModel(rate) if compound else LinearGrowthModel(rate)
