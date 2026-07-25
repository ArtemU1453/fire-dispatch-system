"""DispatchValidator — checks a request is well-formed before running.

Field-level ranges are enforced by Pydantic; this validator covers the
cross-field business rules: a location must be resolvable, and manual constraints
must be self-consistent. Existence checks that need the database (incident type,
organizations) are done by the service.
"""

from __future__ import annotations

from app.core.exceptions import ValidationError
from app.dispatch.schemas.requests import DispatchRequest


class DispatchValidator:
    """Validates a :class:`DispatchRequest`."""

    def validate(self, request: DispatchRequest) -> None:
        errors = list(self._errors(request))
        if errors:
            raise ValidationError("; ".join(errors))

    @staticmethod
    def _errors(request: DispatchRequest):
        has_coords = request.latitude is not None and request.longitude is not None
        if not has_coords and not request.address:
            yield "Provide latitude/longitude or a geocodable address"
        if (request.latitude is None) != (request.longitude is None):
            yield "Both latitude and longitude must be provided together"
