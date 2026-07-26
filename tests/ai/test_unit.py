"""Unit tests for the MockAIProvider, text analysis and provider registry."""

from __future__ import annotations

import pytest

from app.ai.interfaces.results import AICapability
from app.ai.providers import MockAIProvider, default_registry
from app.ai.utils.text_analysis import analyze_text, estimate_confidence
from app.core.exceptions import NotFoundError

FIRE_TEXT = (
    "Здравствуйте, у нас пожар в многоквартирном жилом доме по адресу "
    "улица Ленина, дом 10. Внутри есть люди. Меня зовут Иван Петров, "
    "телефон +7 999 123 45 67."
)


def test_text_analysis_extracts_structure() -> None:
    a = analyze_text(FIRE_TEXT)
    assert a.incident_type_code == "fire"
    assert a.category == "fire"
    assert a.people_inside is True
    # people inside escalates fire from high to critical
    assert a.priority == "critical"
    assert a.address is not None and "Ленина" in a.address
    assert a.phone == "+7 999 123 45 67"
    assert a.reporter_name == "Иван Петров"
    assert "многоквартирный жилой дом" in a.objects
    assert estimate_confidence(a) > 0.7


def test_text_analysis_unknown_defaults_to_other() -> None:
    a = analyze_text("Просто проверка связи.")
    # "проверк" matches the false_alarm rule
    assert a.category in ("false_alarm", "other")


def test_road_accident_detection() -> None:
    a = analyze_text("Произошло ДТП, столкновение двух автомобилей на трассе.")
    assert a.category == "road_accident"
    assert "автомобиль" in a.objects


@pytest.mark.asyncio
async def test_mock_provider_capabilities_and_health() -> None:
    provider = MockAIProvider()
    health = await provider.health_check()
    assert health.healthy is True
    assert AICapability.TRANSCRIBE in health.capabilities
    assert provider.model_version == "1.0.0"


@pytest.mark.asyncio
async def test_mock_provider_transcribe_with_sample() -> None:
    provider = MockAIProvider()
    result = await provider.transcribe(None, sample_text=FIRE_TEXT)
    assert result.text == FIRE_TEXT
    assert result.language == "ru"
    assert result.segments
    assert result.meta is not None
    assert result.meta.model == "mock-dispatch-nlp"
    assert result.meta.processing_ms >= 0


@pytest.mark.asyncio
async def test_mock_provider_extract_classify_summarize() -> None:
    provider = MockAIProvider()
    extraction = await provider.extract_entities(FIRE_TEXT)
    assert extraction.entities.address is not None
    assert extraction.entities.phone == "+7 999 123 45 67"

    classification = await provider.classify_incident(FIRE_TEXT)
    assert classification.category == "fire"
    assert classification.priority == "critical"
    assert classification.meta.provider == "mock"

    summary = await provider.summarize(FIRE_TEXT)
    assert "пожар" in summary.summary.lower()


@pytest.mark.asyncio
async def test_mock_provider_analyze_bundles_everything() -> None:
    provider = MockAIProvider()
    analysis = await provider.analyze(FIRE_TEXT)
    assert analysis.summary
    assert analysis.entities.address is not None
    assert analysis.classification.category == "fire"
    assert analysis.meta is not None


def test_registry_default_and_lookup() -> None:
    registry = default_registry()
    assert registry.default_name == "mock"
    assert "mock" in registry.names()
    assert registry.get().name == "mock"
    assert registry.get("mock").name == "mock"


def test_registry_unknown_provider_raises() -> None:
    registry = default_registry()
    with pytest.raises(NotFoundError):
        registry.get("does-not-exist")
