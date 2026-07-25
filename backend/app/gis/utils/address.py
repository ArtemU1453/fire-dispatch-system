"""Address text utilities: abbreviation dictionaries and tokenization helpers.

Pure, dependency-free functions used by the normalization service. Kept separate
so the vocabulary can grow without touching service logic (DRY).
"""

from __future__ import annotations

import re

# Canonical street/place type words mapped from their common abbreviations.
# Keys are compared without a trailing dot and case-insensitively.
STREET_TYPE_ABBREVIATIONS: dict[str, str] = {
    "ул": "улица",
    "пр-т": "проспект",
    "пр-кт": "проспект",
    "просп": "проспект",
    "пер": "переулок",
    "б-р": "бульвар",
    "бул": "бульвар",
    "бульв": "бульвар",
    "наб": "набережная",
    "пл": "площадь",
    "ш": "шоссе",
    "туп": "тупик",
    "пр-д": "проезд",
    "мкр": "микрорайон",
    "мкрн": "микрорайон",
}

PLACE_TYPE_ABBREVIATIONS: dict[str, str] = {
    "г": "город",
    "обл": "область",
    "р-н": "район",
    "рн": "район",
    "пос": "посёлок",
    "пгт": "посёлок",
    "дер": "деревня",
    "с": "село",
    "респ": "республика",
    "край": "край",
    "тер": "территория",
}

# House/part markers. "д" is resolved contextually (see resolve_token).
UNIT_ABBREVIATIONS: dict[str, str] = {
    "д": "дом",
    "дом": "дом",
    "корп": "корпус",
    "корп-с": "корпус",
    "к": "корпус",
    "стр": "строение",
    "стр-е": "строение",
    "кв": "квартира",
    "оф": "офис",
    "влд": "владение",
}

# All street-type canonical words (for canonical-key stripping).
STREET_TYPE_WORDS = set(STREET_TYPE_ABBREVIATIONS.values()) | {
    "улица",
    "проспект",
    "переулок",
    "бульвар",
    "набережная",
    "площадь",
    "шоссе",
    "тупик",
    "проезд",
    "аллея",
    "линия",
}

_DOT_RE = re.compile(r"\.")
# Dots double as separators so glued abbreviations split cleanly:
# ``д.7`` → ``д 7``, ``г.Москва`` → ``г москва``, ``ул.Ленина`` → ``ул ленина``.
# Hyphenated abbreviations (``пр-т``, ``р-н``) are preserved.
_TOKEN_SPLIT_RE = re.compile(r"[,.\s]+")
# Split a unit abbreviation glued directly to a number: ``д7`` → ``д 7``.
_GLUED_UNIT_RE = re.compile(r"^(д|дом|к|корп|стр|кв|оф|влд)(\d.*)$")
_HAS_DIGIT_RE = re.compile(r"\d")


def strip_dot(token: str) -> str:
    """Remove dots from an abbreviation token."""
    return _DOT_RE.sub("", token)


def tokenize(text: str) -> list[str]:
    """Split an address into lowercase tokens on commas/whitespace/dots."""
    tokens: list[str] = []
    for token in _TOKEN_SPLIT_RE.split(text.strip().lower()):
        if not token:
            continue
        match = _GLUED_UNIT_RE.match(token)
        if match:
            tokens.extend([match.group(1), match.group(2)])
        else:
            tokens.append(token)
    return tokens


def has_digit(token: str) -> bool:
    return bool(_HAS_DIGIT_RE.search(token))


def resolve_token(token: str, next_token: str | None) -> str:
    """Expand a single abbreviation token to its canonical word.

    ``next_token`` disambiguates ``д`` (дом before a number, деревня before a
    word) and similar cases.
    """
    bare = strip_dot(token)
    if bare == "д":
        if next_token is not None and has_digit(next_token):
            return "дом"
        return "деревня"
    if bare in STREET_TYPE_ABBREVIATIONS:
        return STREET_TYPE_ABBREVIATIONS[bare]
    if bare in PLACE_TYPE_ABBREVIATIONS:
        return PLACE_TYPE_ABBREVIATIONS[bare]
    if bare in UNIT_ABBREVIATIONS:
        return UNIT_ABBREVIATIONS[bare]
    return bare
