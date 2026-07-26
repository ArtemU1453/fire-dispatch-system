"""AI providers (the mock, and the registry for connecting more)."""

from __future__ import annotations

from app.ai.providers.mock import MockAIProvider
from app.ai.providers.registry import AIProviderRegistry, default_registry

__all__ = ["AIProviderRegistry", "MockAIProvider", "default_registry"]
