"""Address normalization service.

Turns free-form Russian addresses into a consistent canonical form so that
variants like ``ул Ленина 15``, ``улица Ленина,15`` and ``Ленина 15`` collapse
toward a single representation. Pure and deterministic — no I/O — which makes it
trivially unit-testable and reusable as a cache-key builder.

Two outputs are produced:

- ``normalized`` — human-readable canonical text with abbreviations expanded,
  lowercased, whitespace/punctuation tidied (``улица ленина, 15``).
- ``canonical`` — a comparison key with street-type words removed and tokens
  sorted, so all three examples above map to the same value (``15 ленина``).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.gis.utils.address import STREET_TYPE_WORDS, has_digit, resolve_token, tokenize


@dataclass(slots=True)
class NormalizedAddress:
    """Result of normalizing a raw address string."""

    raw: str
    normalized: str
    canonical: str


class NormalizationService:
    """Canonicalize address strings (stateless, pure)."""

    def normalize(self, raw: str) -> NormalizedAddress:
        tokens = tokenize(raw)
        expanded: list[str] = []
        for i, token in enumerate(tokens):
            nxt = tokens[i + 1] if i + 1 < len(tokens) else None
            expanded.append(resolve_token(token, nxt))

        normalized = self._render(expanded)
        canonical = self._canonical_key(expanded)
        return NormalizedAddress(raw=raw, normalized=normalized, canonical=canonical)

    @staticmethod
    def _render(tokens: list[str]) -> str:
        """Render tokens as ``<words>, <house number>`` when a number trails."""
        if not tokens:
            return ""
        # Split trailing numeric tokens (house number) from the name part.
        head = list(tokens)
        tail: list[str] = []
        while head and has_digit(head[-1]):
            tail.insert(0, head.pop())
        name_part = " ".join(head).strip()
        number_part = " ".join(tail).strip()
        if name_part and number_part:
            return f"{name_part}, {number_part}"
        return name_part or number_part

    @staticmethod
    def _canonical_key(tokens: list[str]) -> str:
        """Order-independent key with street/place type words removed."""
        core = [
            t
            for t in tokens
            if t not in STREET_TYPE_WORDS and t not in {"дом", "город"}
        ]
        return " ".join(sorted(core))
