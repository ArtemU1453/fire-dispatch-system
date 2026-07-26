"""Strategic scenario storage (Stage 18 §9).

Scenarios are stored **separately** from the production database — in process
memory (seeded from the built-in library) or as JSON files. The digital twin
never persists to, or reads from, the live system.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from app.digital_twin.scenarios.schema import Scenario


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
        return [
            Scenario.from_dict(json.loads(p.read_text("utf-8")))
            for p in sorted(self._dir.glob("*.json"))
        ]

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
