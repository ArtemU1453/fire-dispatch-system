"""CapabilityAnalyzer — reasons about capabilities, not unit names.

Determines which capabilities an incident requires (from the consolidated
requirements) and measures how the selected units cover them. Selection is
capability-driven: adding a new capability needs no algorithm change, only a rule
that requires it.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.dispatch.algorithms.candidate import DispatchCandidate
from app.dispatch.recommendations.models import CapabilityCoverage
from app.dispatch.requirements import RequirementSet


class CapabilityAnalyzer:
    """Analyses capability requirements and coverage."""

    def required_codes(self, requirements: RequirementSet) -> list[str]:
        return requirements.required_capability_codes

    def provides_any_required(
        self, candidate: DispatchCandidate, requirements: RequirementSet
    ) -> bool:
        """True if the candidate provides at least one required capability.

        When the incident requires no specific capability, every candidate
        qualifies on capability grounds.
        """
        required = requirements.capabilities
        if not required:
            return True
        return any(candidate.provides(code) for code in required)

    def provided_quantity(
        self, code: str, units: Sequence[DispatchCandidate]
    ) -> int:
        return sum(u.capabilities.get(code, 0) for u in units)

    def coverage(
        self,
        requirements: RequirementSet,
        units: Sequence[DispatchCandidate],
        labels: dict[str, str] | None = None,
    ) -> list[CapabilityCoverage]:
        labels = labels or {}
        coverage: list[CapabilityCoverage] = []
        for need in sorted(
            requirements.capabilities.values(), key=lambda n: n.code
        ):
            coverage.append(
                CapabilityCoverage(
                    code=need.code,
                    label=labels.get(need.code),
                    required=need.min_quantity,
                    provided=self.provided_quantity(need.code, units),
                    mandatory=need.mandatory,
                )
            )
        return coverage
