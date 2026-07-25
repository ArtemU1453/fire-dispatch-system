"""ETA seam re-exported at the service layer (interface only).

Routing / ETA is a later stage; only the interface and a null implementation
exist. See :mod:`app.dispatch.eta`.
"""

from __future__ import annotations

from app.dispatch.eta import ETAProvider, NullETAProvider

__all__ = ["ETAProvider", "NullETAProvider"]
