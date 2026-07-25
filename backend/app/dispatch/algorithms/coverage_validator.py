"""CoverageValidator — decides whether a composition is sufficient.

A composition is *sufficient* when every **mandatory** capability is covered and
the minimum unit count is met. Produces human-readable messages explaining any
shortfall (used both for the response and the persisted log).
"""

from __future__ import annotations

from collections.abc import Sequence

from app.dispatch.recommendations.models import CapabilityCoverage
from app.dispatch.requirements import RequirementSet


class CoverageValidator:
    """Validates capability coverage and unit-count sufficiency."""

    def validate(
        self,
        requirements: RequirementSet,
        primary_count: int,
        coverage: Sequence[CapabilityCoverage],
    ) -> tuple[bool, list[str]]:
        messages: list[str] = []

        if primary_count == 0:
            messages.append("Доступных ресурсов не найдено.")
            return False, messages

        units_ok = primary_count >= requirements.minimum_units
        if not units_ok:
            messages.append(
                f"Недостаточно единиц: подобрано {primary_count} из "
                f"минимально необходимых {requirements.minimum_units}."
            )

        caps_ok = True
        for cov in coverage:
            if cov.mandatory and not cov.satisfied:
                caps_ok = False
                messages.append(
                    f"Не покрыта обязательная возможность "
                    f"«{cov.label or cov.code}»: {cov.provided} из {cov.required}."
                )

        sufficient = units_ok and caps_ok
        if sufficient:
            messages.append("Рекомендация сформирована; требования выполнены.")
        return sufficient, messages
