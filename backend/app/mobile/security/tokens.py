"""Mobile session & token security (Stage 19 §Авторизация, §Безопасность).

Issues opaque session tokens for authenticated users and validates them on each
request. Security properties:
- the raw token is returned to the client once and **never stored** — only its
  SHA-256 hash is kept, so a leak of the store does not expose usable tokens;
- **idle timeout**: a session expires after a period of inactivity
  (auto-logout);
- **remote termination**: an operator can revoke a single session or all of a
  user's sessions.

Passwords are never handled here (and never stored in plaintext anywhere — the
Administration module hashes them with PBKDF2); this layer only manages the
post-authentication session. Authorisation uses the existing RBAC service.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

DEFAULT_IDLE_TTL = timedelta(minutes=30)
DEFAULT_ABSOLUTE_TTL = timedelta(hours=12)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass
class MobileSession:
    token_hash: str
    user_id: str
    app: str
    created_at: datetime
    last_seen: datetime
    expires_at: datetime
    revoked: bool = False
    metadata: dict = field(default_factory=dict)


class SessionExpiredError(RuntimeError):
    pass


class SessionStore:
    """In-memory store of active sessions keyed by token hash."""

    def __init__(
        self,
        idle_ttl: timedelta = DEFAULT_IDLE_TTL,
        absolute_ttl: timedelta = DEFAULT_ABSOLUTE_TTL,
    ) -> None:
        self._sessions: dict[str, MobileSession] = {}
        self._idle_ttl = idle_ttl
        self._absolute_ttl = absolute_ttl

    def create(self, user_id: str, *, app: str = "responder") -> str:
        """Create a session and return the raw token (shown to the client once)."""
        now = datetime.now(tz=UTC)
        raw = secrets.token_urlsafe(32)
        self._sessions[_hash(raw)] = MobileSession(
            token_hash=_hash(raw),
            user_id=user_id,
            app=app,
            created_at=now,
            last_seen=now,
            expires_at=now + self._absolute_ttl,
        )
        return raw

    def validate(self, token: str, *, now: datetime | None = None) -> MobileSession:
        """Return the live session for a token, refreshing last-seen.

        Raises :class:`SessionExpiredError` if unknown, revoked, idle-timed-out
        or past its absolute lifetime.
        """
        now = now or datetime.now(tz=UTC)
        session = self._sessions.get(_hash(token))
        if session is None or session.revoked:
            raise SessionExpiredError("invalid or revoked session")
        if now >= session.expires_at:
            self._sessions.pop(session.token_hash, None)
            raise SessionExpiredError("session expired")
        if now - session.last_seen >= self._idle_ttl:
            self._sessions.pop(session.token_hash, None)
            raise SessionExpiredError("session idle-timeout")
        session.last_seen = now
        return session

    def revoke(self, token: str) -> bool:
        session = self._sessions.get(_hash(token))
        if session is None:
            return False
        session.revoked = True
        return True

    def revoke_all_for_user(self, user_id: str) -> int:
        """Remote termination of every session of a user; returns count revoked."""
        count = 0
        for session in self._sessions.values():
            if session.user_id == user_id and not session.revoked:
                session.revoked = True
                count += 1
        return count

    def active_sessions(self, user_id: str) -> list[MobileSession]:
        return [
            s
            for s in self._sessions.values()
            if s.user_id == user_id and not s.revoked
        ]
