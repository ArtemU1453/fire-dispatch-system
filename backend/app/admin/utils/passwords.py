"""Password hashing and policy validation (stdlib only, no external deps).

Uses PBKDF2-HMAC-SHA256 from the standard library so no new dependency is
introduced. The stored form is ``pbkdf2_sha256$<iterations>$<salt>$<hash>``,
which a real auth backend can later verify or migrate. No real authentication
flow is implemented at this stage — this only lets the admin module create users
with a safely hashed password.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass

_ALGO = "pbkdf2_sha256"
_ITERATIONS = 240_000


def hash_password(password: str, *, iterations: int = _ITERATIONS) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
    ).hex()
    return f"{_ALGO}${iterations}${salt}${digest}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algo, iters, salt, digest = encoded.split("$", 3)
    except ValueError:
        return False
    if algo != _ALGO:
        return False
    computed = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iters)
    ).hex()
    return hmac.compare_digest(computed, digest)


@dataclass(slots=True)
class PasswordRules:
    """The subset of a :class:`PasswordPolicy` used to validate a password."""

    min_length: int = 8
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digit: bool = True
    require_special: bool = False


_SPECIALS = set("!@#$%^&*()_+-=[]{};:,.<>?/|\\\"'`~")


def validate_password(password: str, rules: PasswordRules) -> list[str]:
    """Return a list of human-readable violations (empty = valid)."""
    problems: list[str] = []
    if len(password) < rules.min_length:
        problems.append(f"минимальная длина — {rules.min_length}")
    if rules.require_uppercase and not any(c.isupper() for c in password):
        problems.append("нужна заглавная буква")
    if rules.require_lowercase and not any(c.islower() for c in password):
        problems.append("нужна строчная буква")
    if rules.require_digit and not any(c.isdigit() for c in password):
        problems.append("нужна цифра")
    if rules.require_special and not any(c in _SPECIALS for c in password):
        problems.append("нужен специальный символ")
    return problems
