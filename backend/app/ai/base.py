"""AI provider abstraction.

Defines the boundary between the application and any future AI/ML capability
(routing recommendations, incident classification, etc.). Coding to this
interface (Dependency Inversion) means concrete providers — a local model, an
external API, a rules engine — can be plugged in later without touching callers.

No business logic is implemented yet; this is purely the extension seam.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AIRequest:
    """Generic input envelope for an AI capability."""

    prompt: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AIResponse:
    """Generic output envelope from an AI capability."""

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class AIProvider(ABC):
    """Abstract AI provider interface.

    Concrete implementations live alongside this module and are wired in through
    Dependency Injection.
    """

    @abstractmethod
    async def generate(self, request: AIRequest) -> AIResponse:
        """Produce an :class:`AIResponse` for the given ``request``."""
        raise NotImplementedError
