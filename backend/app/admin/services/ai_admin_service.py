"""AI administration (stage §7).

Lets an administrator view AI providers and their state (health, model versions),
choose the default provider, enable/disable providers and manage AI parameters —
**reusing the Stage-12 AI registry unchanged**. Enable/default/parameters are
stored as ordinary settings (category ``ai``), so nothing in the AI platform is
modified; this module only reads its registry and records the operator's choices.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.schemas.admin import AIProviderAdminResponse, AISettingsResponse
from app.admin.services.settings_service import SettingsService
from app.ai.deps import get_ai_registry
from app.core.exceptions import NotFoundError


class AIAdminService:
    def __init__(self, session: AsyncSession) -> None:
        self._registry = get_ai_registry()
        self._settings = SettingsService(session)

    async def overview(self) -> AISettingsResponse:
        default = await self._setting(
            "ai.default_provider", self._registry.default_name
        )
        params = await self._setting("ai.parameters", {})
        providers: list[AIProviderAdminResponse] = []
        for provider in self._registry.all():
            health = await provider.health_check()
            enabled = await self._setting(
                f"ai.provider.{provider.name}.enabled", True
            )
            providers.append(
                AIProviderAdminResponse(
                    name=provider.name,
                    model=provider.model,
                    model_version=provider.model_version,
                    capabilities=[c.value for c in provider.capabilities],
                    healthy=health.healthy,
                    is_default=(provider.name == default),
                    is_enabled=bool(enabled),
                )
            )
        return AISettingsResponse(
            default_provider=default,
            providers=providers,
            parameters=params if isinstance(params, dict) else {},
        )

    async def _setting(self, key: str, default):
        """Read a setting's typed value, or return ``default`` if unset."""
        try:
            return await self._settings.typed_value(key)
        except NotFoundError:
            return default
