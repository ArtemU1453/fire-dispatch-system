"""Unit tests for address normalization (pure, hermetic)."""

from __future__ import annotations

import pytest

from app.gis.services.normalization import NormalizationService

svc = NormalizationService()


def test_variants_of_same_address_share_canonical_key() -> None:
    forms = ["ул Ленина 15", "улица Ленина,15", "Ленина 15", "УЛ. ЛЕНИНА 15"]
    keys = {svc.normalize(f).canonical for f in forms}
    assert len(keys) == 1


def test_typed_variants_share_normalized_text() -> None:
    a = svc.normalize("ул Ленина 15").normalized
    b = svc.normalize("улица Ленина,15").normalized
    assert a == b == "улица ленина, 15"


@pytest.mark.parametrize(
    "raw, expected_substring",
    [
        ("ул. Тверская", "улица"),
        ("пр-т Мира", "проспект"),
        ("пер. Кривой", "переулок"),
        ("наб. Фонтанки", "набережная"),
        ("б-р Гоголя", "бульвар"),
    ],
)
def test_street_type_abbreviations_expand(raw: str, expected_substring: str) -> None:
    assert expected_substring in svc.normalize(raw).normalized


def test_house_marker_with_number_becomes_dom() -> None:
    # "д" before a number → "дом"; glued forms are split too.
    assert "дом" in svc.normalize("Ленина д 5").normalized
    assert "дом" in svc.normalize("Ленина д.5").normalized
    assert "дом" in svc.normalize("Ленина д5").normalized


def test_glued_city_prefix_splits() -> None:
    a = svc.normalize("г.Москва, ул.Тверская, д.7").normalized
    b = svc.normalize("г. Москва, ул. Тверская, д. 7").normalized
    assert a == b
    assert "город москва" in a


def test_empty_input_is_safe() -> None:
    result = svc.normalize("   ")
    assert result.normalized == ""
    assert result.canonical == ""


def test_house_number_placed_after_comma() -> None:
    assert svc.normalize("улица Ленина 15").normalized.endswith(", 15")
