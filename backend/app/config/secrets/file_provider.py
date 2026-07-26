"""File-based secrets provider (Docker / Kubernetes / systemd credentials).

Container orchestrators mount each secret as a file (``/run/secrets/<key>`` for
Docker Swarm and Compose, projected volumes for Kubernetes, ``$CREDENTIALS_
DIRECTORY`` for systemd). This provider reads the file named after the key and
returns its trimmed contents, so secrets never appear in the environment table
or the process command line.
"""

from __future__ import annotations

from pathlib import Path

from app.config.secrets.base import SecretsProvider


class FileSecretsProvider(SecretsProvider):
    """Resolve secrets from individual files under a directory."""

    name = "file"

    def __init__(self, directory: str | Path) -> None:
        self._dir = Path(directory)

    def _lookup(self, key: str) -> str | None:
        # Guard against path traversal: only a bare file name is honoured.
        if "/" in key or "\\" in key or key in ("", ".", ".."):
            return None
        path = self._dir / key
        try:
            # ``strip`` drops the trailing newline editors/orchestrators add.
            return path.read_text(encoding="utf-8").strip()
        except (FileNotFoundError, IsADirectoryError, PermissionError):
            return None
