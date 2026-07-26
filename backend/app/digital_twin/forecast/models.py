"""Forecasting models (Stage 18 §6).

Simple, transparent statistical models — no ML, no black boxes. The interface is
pluggable so more sophisticated models can be added later without changing
callers. Used to project load growth, call-volume change, population density
change and transport-accessibility change over a horizon.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class ProjectionPoint:
    year: int
    value: float


class GrowthModel(Protocol):
    def project(self, base_value: float, years: int) -> list[ProjectionPoint]: ...


@dataclass
class LinearGrowthModel:
    """value(t) = base * (1 + rate * t) — steady absolute-rate growth."""

    annual_rate: float = 0.03

    def project(self, base_value: float, years: int) -> list[ProjectionPoint]:
        return [
            ProjectionPoint(
                year=t, value=round(base_value * (1 + self.annual_rate * t), 2)
            )
            for t in range(years + 1)
        ]


@dataclass
class CompoundGrowthModel:
    """value(t) = base * (1 + rate)^t — compounding growth."""

    annual_rate: float = 0.03

    def project(self, base_value: float, years: int) -> list[ProjectionPoint]:
        return [
            ProjectionPoint(
                year=t, value=round(base_value * (1 + self.annual_rate) ** t, 2)
            )
            for t in range(years + 1)
        ]
