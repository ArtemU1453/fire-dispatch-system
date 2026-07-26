"""Scenario storage (Stage 17 §5, §8).

Scenarios live in the **training contour only** — never in the production
database. Two interchangeable stores are provided:

* :class:`InMemoryScenarioStore` — process-memory, seeded from the built-in
  library; the default, fully isolated and dependency-free.
* :class:`FileScenarioStore` — JSON files in a dedicated directory, so authored
  scenarios can be recorded and replayed across restarts.

Both implement the same small interface, so the service layer is agnostic.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from app.simulator.scenarios.schema import Scenario


class ScenarioNotFoundError(KeyError):
    def __init__(self, scenario_id: str) -> None:
        super().__init__(scenario_id)
        self.scenario_id = scenario_id


class ScenarioStore(Protocol):
    def list(self) -> list[Scenario]: ...
    def get(self, scenario_id: str) -> Scenario: ...
    def save(self, scenario: Scenario) -> Scenario: ...
    def delete(self, scenario_id: str) -> None: ...


class InMemoryScenarioStore:
    """Dictionary-backed store, optionally seeded with scenarios."""

    def __init__(self, seed: list[Scenario] | None = None) -> None:
        self._items: dict[str, Scenario] = {}
        for s in seed or ():
            self._items[s.id] = s

    def list(self) -> list[Scenario]:
        return sorted(self._items.values(), key=lambda s: s.id)

    def get(self, scenario_id: str) -> Scenario:
        try:
            return self._items[scenario_id]
        except KeyError as exc:
            raise ScenarioNotFoundError(scenario_id) from exc

    def save(self, scenario: Scenario) -> Scenario:
        self._items[scenario.id] = scenario
        return scenario

    def delete(self, scenario_id: str) -> None:
        if scenario_id not in self._items:
            raise ScenarioNotFoundError(scenario_id)
        del self._items[scenario_id]


class FileScenarioStore:
    """JSON-file-backed store in a dedicated directory (one file per scenario)."""

    def __init__(
        self, directory: str | Path, seed: list[Scenario] | None = None
    ) -> None:
        self._dir = Path(directory)
        self._dir.mkdir(parents=True, exist_ok=True)
        for s in seed or ():
            if not self._path(s.id).exists():
                self.save(s)

    def _path(self, scenario_id: str) -> Path:
        safe = scenario_id.replace("/", "_").replace("\\", "_")
        return self._dir / f"{safe}.json"

    def list(self) -> list[Scenario]:
        out: list[Scenario] = []
        for path in sorted(self._dir.glob("*.json")):
            out.append(Scenario.from_dict(json.loads(path.read_text("utf-8"))))
        return out

    def get(self, scenario_id: str) -> Scenario:
        path = self._path(scenario_id)
        if not path.exists():
            raise ScenarioNotFoundError(scenario_id)
        return Scenario.from_dict(json.loads(path.read_text("utf-8")))

    def save(self, scenario: Scenario) -> Scenario:
        self._path(scenario.id).write_text(
            json.dumps(scenario.to_dict(), ensure_ascii=False, indent=2), "utf-8"
        )
        return scenario

    def delete(self, scenario_id: str) -> None:
        path = self._path(scenario_id)
        if not path.exists():
            raise ScenarioNotFoundError(scenario_id)
        path.unlink()
