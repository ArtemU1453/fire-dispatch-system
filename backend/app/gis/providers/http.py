"""Shared HTTP plumbing for network-backed geocoding providers.

Centralises ``httpx.AsyncClient`` lifecycle, timeout, user-agent and JSON GET
handling so each concrete provider only implements request building and response
mapping (DRY). The client is created lazily and can be injected in tests.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.gis.providers.base import GeoProvider, GeoProviderError


class HttpGeoProvider(GeoProvider):
    """Base class for providers that call an HTTP JSON API."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 10.0,
        user_agent: str = "ai-dispatcher-mchs",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._user_agent = user_agent
        self._client = client
        self._owns_client = client is None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                headers={"User-Agent": self._user_agent},
            )
        return self._client

    async def _get_json(self, path: str, params: dict[str, Any]) -> Any:
        """Perform a GET and return parsed JSON, translating failures."""
        url = f"{self._base_url}{path}"
        try:
            response = await self._get_client().get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise GeoProviderError(f"{self.name}: HTTP request failed: {exc}") from exc
        except ValueError as exc:  # JSON decode
            raise GeoProviderError(f"{self.name}: invalid JSON response") from exc

    async def aclose(self) -> None:
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None
