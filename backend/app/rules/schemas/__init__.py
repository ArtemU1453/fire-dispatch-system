"""Rules API schemas."""

from app.rules.schemas.content import (
    ActionInput,
    ActionResponse,
    CapabilityRequirementInput,
    CapabilityRequirementResponse,
    ConditionInput,
    ConditionResponse,
    ResourceRequirementInput,
    ResourceRequirementResponse,
    VersionContentInput,
)
from app.rules.schemas.rule import (
    RuleCategoryCreate,
    RuleCategoryResponse,
    RuleCategoryUpdate,
    RuleCreate,
    RuleResponse,
    RuleSetCreate,
    RuleSetResponse,
    RuleSetUpdate,
    RuleSummaryResponse,
    RuleUpdate,
    RuleVersionResponse,
    RuleVersionSummary,
)
from app.rules.schemas.service import CompositionItem, RequirementsResponse

__all__ = [
    # content
    "ConditionInput", "ConditionResponse",
    "ActionInput", "ActionResponse",
    "ResourceRequirementInput", "ResourceRequirementResponse",
    "CapabilityRequirementInput", "CapabilityRequirementResponse",
    "VersionContentInput",
    # rule / version
    "RuleCreate", "RuleUpdate", "RuleResponse", "RuleSummaryResponse",
    "RuleVersionResponse", "RuleVersionSummary",
    # category / set
    "RuleCategoryCreate", "RuleCategoryUpdate", "RuleCategoryResponse",
    "RuleSetCreate", "RuleSetUpdate", "RuleSetResponse",
    # service
    "RequirementsResponse", "CompositionItem",
]
