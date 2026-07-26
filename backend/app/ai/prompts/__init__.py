"""Prompt templates for AI capabilities (used by real LLM providers)."""

from __future__ import annotations

from app.ai.prompts.templates import (
    SYSTEM_DISPATCH_ASSISTANT,
    classify_incident_prompt,
    extract_entities_prompt,
    summarize_prompt,
    transcribe_prompt,
)

__all__ = [
    "SYSTEM_DISPATCH_ASSISTANT",
    "classify_incident_prompt",
    "extract_entities_prompt",
    "summarize_prompt",
    "transcribe_prompt",
]
