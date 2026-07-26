"""Administrative audit (reuses the existing audit_logs trail)."""

from __future__ import annotations

from app.admin.audit.recorder import AdminAuditRecorder, diff

__all__ = ["AdminAuditRecorder", "diff"]
