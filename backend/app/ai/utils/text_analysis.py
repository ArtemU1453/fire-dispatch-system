"""Deterministic, offline text analysis for the mock AI provider.

Pure keyword / regex heuristics over Russian emergency-call text — **no ML, no
network**. This lives behind the ``AIProvider`` interface, so replacing it with a
real model changes nothing for callers. It exists so the mock produces
plausible, testable suggestions (address, incident type, category, priority,
objects, phone, reporter).

The category / priority label values match the incident module's enums, but this
module only *suggests* them — it never imports or mutates any incident entity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---- incident detection ---------------------------------------------------
# Each rule: keywords → (type code, type name, category, priority).
_INCIDENT_RULES: list[tuple[tuple[str, ...], str, str, str, str]] = [
    (("взрыв", "взорвал"), "explosion", "Взрыв", "fire", "critical"),
    (("пожар", "горит", "возгоран", "задымлен", "дым", "огонь"),
     "fire", "Пожар", "fire", "high"),
    (("дтп", "авари", "столкновен", "сбил", "машина перевернул"),
     "road_accident", "ДТП", "road_accident", "high"),
    (("утечк", "газ", "хлор", "аммиак", "химическ", "разлив"),
     "chemical", "Химическая опасность", "chemical", "critical"),
    (("тонет", "утопающ", "провалил", "застрял", "завал", "спасти", "спасен"),
     "rescue", "Спасательные работы", "rescue", "high"),
    (("лес", "трав", "камыш", "поле горит"),
     "wildfire", "Природный пожар", "wildfire", "normal"),
    (("проверк", "ложн", "ошибочн"),
     "false_alarm", "Ложный вызов", "false_alarm", "low"),
]

# Objects that may be mentioned (label → keywords).
_OBJECT_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("многоквартирный жилой дом", ("многоквартир", "жилой дом", "квартир")),
    ("частный дом", ("частн", "коттедж")),
    ("школа", ("школ",)),
    ("больница", ("больниц", "госпитал", "поликлиник")),
    ("детский сад", ("детск", "садик")),
    ("торговый центр", ("торгов", "тц", "магазин")),
    ("автомобиль", ("автомобил", "машин", "авто")),
    ("промышленный объект", ("завод", "цех", "склад", "фабрик")),
]

_PEOPLE_INSIDE = ("люди внутри", "человек внутри", "внутри люди", "есть люди",
                  "остались люди", "ребёнок", "ребенок", "дети")

_ADDRESS_RE = re.compile(
    r"(?:ул(?:ица|\.)?|просп(?:ект|\.)?|пер(?:еулок|\.)?|пл(?:ощадь|\.)?|"
    r"ш(?:оссе|\.)?|бульвар|б-р|наб(?:ережная|\.)?)\s+"
    r"[А-ЯЁ][А-Яа-яё\-]+(?:\s+[А-ЯЁа-яё\-]+){0,2}"
    r"(?:,?\s*(?:д(?:ом)?\.?)\s*\d+[А-Яа-я]?)?"
    r"(?:,?\s*(?:кв(?:артира)?\.?)\s*\d+)?",
    re.IGNORECASE,
)
_PHONE_RE = re.compile(
    r"(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}"
)
_NAME_RE = re.compile(
    r"(?:[Мм]еня зовут|[Мм]оя фамилия|[Зз]аявитель|[Зз]вонит)\s+"
    r"([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+){0,2})"
)


@dataclass(slots=True)
class TextAnalysis:
    address: str | None = None
    incident_type_code: str | None = None
    incident_type_name: str | None = None
    category: str = "other"
    priority: str = "normal"
    objects: list[str] = field(default_factory=list)
    phone: str | None = None
    reporter_name: str | None = None
    people_inside: bool = False
    matched_keywords: list[str] = field(default_factory=list)


def _lower(text: str) -> str:
    return text.lower().replace("ё", "е")


def detect_incident(text: str) -> tuple[str | None, str | None, str, str, list[str]]:
    low = _lower(text)
    for keywords, code, name, category, priority in _INCIDENT_RULES:
        hit = [k for k in keywords if _lower(k) in low]
        if hit:
            return code, name, category, priority, hit
    return None, None, "other", "normal", []


def extract_objects(text: str) -> list[str]:
    low = _lower(text)
    found: list[str] = []
    for label, keywords in _OBJECT_RULES:
        if any(_lower(k) in low for k in keywords):
            found.append(label)
    return found


def extract_address(text: str) -> str | None:
    match = _ADDRESS_RE.search(text)
    if not match:
        return None
    return " ".join(match.group(0).split()).strip(" ,")


def extract_phone(text: str) -> str | None:
    match = _PHONE_RE.search(text)
    return match.group(0) if match else None


def extract_reporter_name(text: str) -> str | None:
    match = _NAME_RE.search(text)
    return match.group(1).strip() if match else None


def has_people_inside(text: str) -> bool:
    low = _lower(text)
    return any(_lower(p) in low for p in _PEOPLE_INSIDE)


def analyze_text(text: str) -> TextAnalysis:
    code, name, category, priority, keywords = detect_incident(text)
    people = has_people_inside(text)
    # People reported inside a fire escalates the suggested priority.
    if people and priority in ("normal", "high"):
        priority = "critical"
    return TextAnalysis(
        address=extract_address(text),
        incident_type_code=code,
        incident_type_name=name,
        category=category,
        priority=priority,
        objects=extract_objects(text),
        phone=extract_phone(text),
        reporter_name=extract_reporter_name(text),
        people_inside=people,
        matched_keywords=keywords,
    )


def estimate_confidence(analysis: TextAnalysis) -> float:
    """A crude confidence score from how much structure we recognised."""
    score = 0.4
    if analysis.incident_type_code:
        score += 0.3
    if analysis.address:
        score += 0.2
    if analysis.objects:
        score += 0.05
    if analysis.phone or analysis.reporter_name:
        score += 0.05
    return round(min(score, 0.98), 2)
