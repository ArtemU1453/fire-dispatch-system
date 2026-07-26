"""A registry of AI providers.

Holds the available :class:`AIProvider` implementations by name and exposes a
**default**. This is the seam that lets **several providers be connected at
once** (stage "next-stage prep") and selected per request, without any business
logic change — services ask the registry for a provider, never construct one.
"""

from __future__ import annotations

from app.ai.interfaces.provider import AIProvider
from app.core.exceptions import NotFoundError


class AIProviderRegistry:
    """Named collection of AI providers with a designated default."""

    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}
        self._default: str | None = None

    def register(self, provider: AIProvider, *, default: bool = False) -> None:
        self._providers[provider.name] = provider
        if default or self._default is None:
            self._default = provider.name

    def get(self, name: str | None = None) -> AIProvider:
        key = name or self._default
        if key is None:
            raise NotFoundError("No AI provider registered")
        provider = self._providers.get(key)
        if provider is None:
            raise NotFoundError(f"AI provider not found: {key}")
        return provider

    def names(self) -> list[str]:
        return list(self._providers.keys())

    def all(self) -> list[AIProvider]:
        return list(self._providers.values())

    @property
    def default_name(self) -> str | None:
        return self._default


def default_registry() -> AIProviderRegistry:
    """A registry pre-loaded with the mock provider (the only one this stage)."""
    from app.ai.providers.mock import MockAIProvider

    registry = AIProviderRegistry()
    registry.register(MockAIProvider(), default=True)
    return registry
