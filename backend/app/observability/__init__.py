"""Observability platform — health, metrics, logging, tracing and alerts.

Provides real-time control of every component's state and diagnostics through a
single set of interfaces (HealthProvider, metrics registry, structured logging,
Trace IDs, alert rules), independent of any monitoring product. It observes the
existing modules without changing their business logic.
"""

from __future__ import annotations

from app.observability.state import install

__all__ = ["install"]
