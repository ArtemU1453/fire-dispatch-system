"""Integration management (stage §6).

Stores connection parameters for external integrations. **Secrets are never
stored in clear text** — a secret is referenced by ``secret_ref`` / a config
marked ``is_secret`` holds only a reference (a pointer into a future secret
manager), and responses mask them. Includes a (mock) health-check.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.admin.audit import AdminAuditRecorder, diff
from app.admin.models.entities import (
    Integration,
    IntegrationConfiguration,
    IntegrationHealthCheck,
    IntegrationProvider,
)
from app.admin.models.enums import HealthStatus, IntegrationStatus
from app.admin.schemas.admin import IntegrationCreate, IntegrationUpdate
from app.admin.utils.actor import Actor
from app.core.exceptions import ConflictError, NotFoundError
from app.models.enums import AuditAction

_TRACKED = ("name", "description", "is_enabled", "status")


class IntegrationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AdminAuditRecorder(session)

    def _load_options(self) -> list:
        return [
            selectinload(Integration.configurations),
            selectinload(Integration.health_checks),
        ]

    async def list_integrations(self) -> Sequence[Integration]:
        stmt = (
            select(Integration)
            .where(Integration.is_deleted.is_(False))
            .order_by(Integration.code)
            .options(*self._load_options())
        )
        return (await self._session.execute(stmt)).scalars().all()

    async def get_integration(self, integration_id: UUID) -> Integration:
        stmt = (
            select(Integration)
            .where(
                Integration.id == integration_id,
                Integration.is_deleted.is_(False),
            )
            .options(*self._load_options())
        )
        integration = (await self._session.execute(stmt)).scalars().first()
        if integration is None:
            raise NotFoundError("Integration not found")
        return integration

    async def list_providers(self) -> Sequence[IntegrationProvider]:
        stmt = (
            select(IntegrationProvider)
            .where(IntegrationProvider.is_deleted.is_(False))
            .order_by(IntegrationProvider.code)
        )
        return (await self._session.execute(stmt)).scalars().all()

    async def create_integration(self, data: IntegrationCreate) -> Integration:
        if await self._by_code(data.code) is not None:
            raise ConflictError(f"Integration code already exists: {data.code}")
        actor = Actor(name=data.actor_name)
        integration = Integration(
            code=data.code,
            name=data.name,
            provider_id=data.provider_id,
            description=data.description,
            is_enabled=data.is_enabled,
            secret_ref=data.secret_ref,
            config=data.config,
            status=IntegrationStatus.INACTIVE,
        )
        for cfg in data.configurations:
            integration.configurations.append(
                IntegrationConfiguration(
                    key=cfg.key, value=cfg.value, is_secret=cfg.is_secret
                )
            )
        self._session.add(integration)
        await self._session.flush()
        self._audit.record(
            AuditAction.CREATE, "integration", entity_id=integration.id,
            changes={"code": data.code}, actor=actor,
        )
        await self._session.flush()
        return await self.get_integration(integration.id)

    async def update_integration(
        self, integration_id: UUID, data: IntegrationUpdate
    ) -> Integration:
        integration = await self.get_integration(integration_id)
        actor = Actor(name=data.actor_name)
        payload = data.model_dump(
            exclude_unset=True,
            exclude={"actor_name", "reason", "configurations", "config",
                     "secret_ref", "provider_id"},
        )
        before = {f: _plain(getattr(integration, f)) for f in _TRACKED}
        for field in _TRACKED:
            if field in payload:
                setattr(integration, field, payload[field])
        after = {f: _plain(getattr(integration, f)) for f in _TRACKED}
        changes = diff(before, after)

        if "provider_id" in data.model_fields_set:
            integration.provider_id = data.provider_id
        if data.config is not None:
            integration.config = data.config
            changes["config"] = {"new": "updated"}
        if data.secret_ref is not None:
            integration.secret_ref = data.secret_ref
            changes["secret_ref"] = {"new": "***"}
        if data.configurations is not None:
            await self._replace_configs(integration, data.configurations)
            changes["configurations"] = {"new": "updated"}

        if changes:
            self._audit.record(
                AuditAction.UPDATE, "integration", entity_id=integration.id,
                changes=changes, reason=data.reason, actor=actor,
            )
        await self._session.flush()
        return await self.get_integration(integration_id)

    async def health_check(self, integration_id: UUID) -> IntegrationHealthCheck:
        """Mock health-check — no real network call at this stage."""
        integration = await self.get_integration(integration_id)
        start = time.perf_counter()
        if integration.is_enabled:
            status = HealthStatus.HEALTHY
            integration.status = IntegrationStatus.ACTIVE
            detail = "enabled (mock check)"
        else:
            status = HealthStatus.UNKNOWN
            integration.status = IntegrationStatus.INACTIVE
            detail = "disabled"
        check = IntegrationHealthCheck(
            integration_id=integration.id,
            status=status,
            latency_ms=max(0, int((time.perf_counter() - start) * 1000)),
            detail=detail,
        )
        self._session.add(check)
        await self._session.flush()
        return check

    def latest_health(
        self, integration: Integration
    ) -> IntegrationHealthCheck | None:
        checks = [c for c in integration.health_checks if not c.is_deleted]
        if not checks:
            return None
        return max(checks, key=lambda c: c.checked_at)

    # ------------------------------------------------------------ helpers
    async def _replace_configs(self, integration, configs) -> None:
        for cfg in list(integration.configurations):
            await self._session.delete(cfg)
        await self._session.flush()
        for cfg in configs:
            integration.configurations.append(
                IntegrationConfiguration(
                    key=cfg.key, value=cfg.value, is_secret=cfg.is_secret
                )
            )

    async def _by_code(self, code: str) -> Integration | None:
        stmt = select(Integration).where(
            Integration.code == code, Integration.is_deleted.is_(False)
        )
        return (await self._session.execute(stmt)).scalars().first()


def _plain(value):
    return value.value if hasattr(value, "value") else value
