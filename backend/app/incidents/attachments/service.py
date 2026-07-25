"""Attachment metadata service (architecture only — no binary storage yet).

This stage delivers the *architecture* for attachments: metadata records
(filename, kind, content type, size and a ``storage_ref`` pointer). Actual file
storage (object store / disk) is intentionally out of scope and plugs in behind
``storage_ref`` later without schema changes.
"""

from __future__ import annotations

from app.incidents.models.entities import Incident, IncidentAttachment
from app.incidents.models.enums import AttachmentKind, TimelineEventType
from app.incidents.timeline import TimelineRecorder
from app.incidents.utils.actor import Actor


class AttachmentService:
    """Registers attachment metadata on an incident."""

    def __init__(self, timeline: TimelineRecorder | None = None) -> None:
        self._timeline = timeline or TimelineRecorder()

    def add(
        self,
        incident: Incident,
        *,
        filename: str,
        kind: AttachmentKind = AttachmentKind.OTHER,
        content_type: str | None = None,
        size_bytes: int | None = None,
        storage_ref: str | None = None,
        description: str | None = None,
        actor: Actor | None = None,
    ) -> IncidentAttachment:
        attachment = IncidentAttachment(
            kind=kind,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            storage_ref=storage_ref,
            description=description,
            uploaded_by_user_id=actor.user_id if actor else None,
        )
        incident.attachments.append(attachment)
        self._timeline.record(
            incident,
            TimelineEventType.ATTACHMENT_ADDED,
            f"Добавлено вложение: {filename}",
            actor=actor,
        )
        return attachment
