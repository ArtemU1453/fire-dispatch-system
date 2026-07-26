"""Prompt templates for AI capabilities.

The ``MockAIProvider`` does not use these (it is offline / deterministic), but a
real LLM provider (OpenAI / Azure / local) builds its prompts here — keeping
prompt engineering in one place, separate from business logic. Templates are
plain builders so they can be versioned and A/B tested later.

Prompt text itself is **never written to the audit log** (stage §12).
"""

from __future__ import annotations

SYSTEM_DISPATCH_ASSISTANT = (
    "Ты — ассистент диспетчера МЧС. Ты анализируешь текст телефонного "
    "разговора и предлагаешь диспетчеру структурированную информацию. "
    "Ты НИКОГДА не принимаешь решений и не выполняешь действий — только "
    "предлагаешь. Окончательное решение всегда за диспетчером."
)


def extract_entities_prompt(text: str, *, language: str = "ru") -> str:
    return (
        f"[{language}] Извлеки из разговора: адрес, тип происшествия, "
        "категорию, упомянутые объекты, телефон, ФИО заявителя и "
        "дополнительные признаки. Верни строгий JSON. Текст:\n"
        f"{text}"
    )


def classify_incident_prompt(text: str, *, language: str = "ru") -> str:
    return (
        f"[{language}] Предложи тип происшествия, категорию и приоритет "
        "(low/normal/high/critical). Это рекомендация, не решение. Текст:\n"
        f"{text}"
    )


def summarize_prompt(text: str, *, language: str = "ru") -> str:
    return (
        f"[{language}] Составь краткое описание разговора в 1–2 предложениях "
        "для диспетчера. Текст:\n"
        f"{text}"
    )


def transcribe_prompt(language: str | None) -> str:
    return f"Transcribe the audio to text ({language or 'auto'} language)."
