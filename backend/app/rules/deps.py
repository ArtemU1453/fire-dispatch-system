"""Rules dependency providers (Dependency Injection wiring)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.deps import SessionDep
from app.rules.services import RuleService


def get_rule_service(session: SessionDep) -> RuleService:
    return RuleService(session)


RuleServiceDep = Annotated[RuleService, Depends(get_rule_service)]
