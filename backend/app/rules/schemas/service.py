"""Schemas returned by the Rule Service (ready-made requirements)."""

from __future__ import annotations

from uuid import UUID

from app.models.enums import ResourceCategory
from app.rules.schemas.content import (
    CapabilityRequirementResponse,
    ResourceRequirementResponse,
)
from app.schemas.common import SchemaBase


class CompositionItem(SchemaBase):
    resource_category: ResourceCategory
    count: int


class RequirementsResponse(SchemaBase):
    """The consolidated requirements a downstream algorithm consumes."""

    rule_id: UUID
    rule_code: str
    version_number: int
    resource_requirements: list[ResourceRequirementResponse]
    capability_requirements: list[CapabilityRequirementResponse]
    minimum_composition: list[CompositionItem]
    recommended_composition: list[CompositionItem]
    reserve_composition: list[CompositionItem]
    required_capabilities: list[str]
