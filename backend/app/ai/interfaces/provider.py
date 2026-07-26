"""The unified ``AIProvider`` interface (stage §2).

Every AI backend — the mock, OpenAI, Azure OpenAI, a local LLM, a specialised
speech-recognition model — implements this one interface. Business logic (the
services) depends only on this abstraction, so **swapping the model never touches
the business logic** (Dependency Inversion).

All methods are async so a real provider can perform network / GPU I/O. Inputs
are plain values (audio reference, text); outputs are the dataclasses in
:mod:`app.ai.interfaces.results`, each stamped with an :class:`AIResultMeta`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.ai.interfaces.results import (
    AICapability,
    AnalysisResult,
    ClassificationResult,
    EntityExtractionResult,
    ProviderHealth,
    SummaryResult,
    TranscriptionResult,
)


class AIProvider(ABC):
    """Abstract interface every AI provider must implement."""

    #: A stable provider identifier (e.g. ``"mock"``, ``"openai"``).
    name: str = "base"
    #: The model this provider instance uses.
    model: str = "base"
    #: The model version (for audit / model-version journaling).
    model_version: str = "0"
    #: The capabilities this provider supports.
    capabilities: tuple[AICapability, ...] = ()

    @abstractmethod
    async def transcribe(
        self,
        audio_ref: str | None,
        *,
        language: str | None = None,
        sample_text: str | None = None,
    ) -> TranscriptionResult:
        """Transcribe an audio reference into text with segments / confidence.

        ``sample_text`` lets a caller feed known text to a mock / offline
        provider (no real audio pipeline at this stage).
        """

    @abstractmethod
    async def extract_entities(
        self, text: str, *, language: str = "ru"
    ) -> EntityExtractionResult:
        """Extract address / type / phone / reporter / objects from a text."""

    @abstractmethod
    async def classify_incident(
        self, text: str, *, language: str = "ru"
    ) -> ClassificationResult:
        """Suggest an incident type, category and priority for a text."""

    @abstractmethod
    async def summarize(
        self, text: str, *, language: str = "ru"
    ) -> SummaryResult:
        """Produce a short human-readable summary of the conversation."""

    @abstractmethod
    async def analyze(
        self, text: str, *, language: str = "ru"
    ) -> AnalysisResult:
        """Combined analysis: summary + entities + classification."""

    @abstractmethod
    async def health_check(self) -> ProviderHealth:
        """Report whether the provider is reachable / operational."""
