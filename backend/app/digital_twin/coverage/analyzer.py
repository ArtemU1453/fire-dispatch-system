"""Coverage analysis (Stage 18 §3).

Given a :class:`TwinModel`, compute:
- arrival time to each district and to a sampling grid over the territory;
- percentage of territory / population covered within the response norm;
- risk zones (poorly-covered areas weighted by protected-object risk);
- unreachable districts (no station within the norm);
- overlap of responsibility zones (points reachable by 2+ stations in norm).

All arithmetic is local and deterministic — no production data, no GIS.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.digital_twin.simulation.model import District, Station, TwinModel


@dataclass
class DistrictCoverage:
    district_id: str
    name: str
    nearest_station_id: str | None
    arrival_time_s: float | None
    covered: bool                 # arrival within the district norm
    responders_in_norm: int       # stations able to reach within norm (overlap)


@dataclass
class CoverageResult:
    territory_covered_pct: float = 0.0
    population_covered_pct: float = 0.0
    avg_arrival_time_s: float | None = None
    unreachable_districts: list[str] = field(default_factory=list)
    risk_zones: list[str] = field(default_factory=list)
    overlap_pct: float = 0.0
    per_district: list[DistrictCoverage] = field(default_factory=list)
    grid_size: int = 0

    def to_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items() if k != "per_district"}
        d["per_district"] = [c.__dict__ for c in self.per_district]
        return d


def _nearest(
    stations: list[Station], model: TwinModel, x: float, y: float
) -> tuple[Station | None, float | None]:
    best: Station | None = None
    best_t: float | None = None
    for s in stations:
        t = model.road.travel_time_s(s.x, s.y, x, y)
        if best_t is None or t < best_t:
            best, best_t = s, t
    return best, best_t


def _responders_within(
    stations: list[Station], model: TwinModel, x: float, y: float, norm_s: float
) -> int:
    return sum(
        1 for s in stations if model.road.travel_time_s(s.x, s.y, x, y) <= norm_s
    )


class CoverageAnalyzer:
    def __init__(self, grid_step_km: float = 3.0) -> None:
        self.grid_step_km = grid_step_km

    def analyze(self, model: TwinModel) -> CoverageResult:
        stations = model.active_stations()
        result = CoverageResult()

        # --- per-district coverage (population & responsibility overlap) ------
        pop_total = 0
        pop_covered = 0
        arrivals: list[float] = []
        overlapping_districts = 0
        for d in model.districts.values():
            nearest, t = _nearest(stations, model, d.x, d.y)
            covered = t is not None and t <= d.norm_time_s
            responders = _responders_within(stations, model, d.x, d.y, d.norm_time_s)
            if t is not None:
                arrivals.append(t)
            pop_total += d.population
            if covered:
                pop_covered += d.population
            if responders >= 2:
                overlapping_districts += 1
            if not covered:
                result.unreachable_districts.append(d.id)
            result.per_district.append(
                DistrictCoverage(
                    district_id=d.id,
                    name=d.name,
                    nearest_station_id=nearest.id if nearest else None,
                    arrival_time_s=round(t, 1) if t is not None else None,
                    covered=covered,
                    responders_in_norm=responders,
                )
            )

        # --- territory coverage via a uniform sampling grid -------------------
        covered_cells, total_cells, overlap_cells = self._grid_coverage(
            model, stations
        )
        result.grid_size = total_cells
        result.territory_covered_pct = (
            round(100.0 * covered_cells / total_cells, 1) if total_cells else 0.0
        )
        result.overlap_pct = (
            round(100.0 * overlap_cells / total_cells, 1) if total_cells else 0.0
        )
        result.population_covered_pct = (
            round(100.0 * pop_covered / pop_total, 1) if pop_total else 0.0
        )
        result.avg_arrival_time_s = (
            round(sum(arrivals) / len(arrivals), 1) if arrivals else None
        )
        result.risk_zones = self._risk_zones(model, stations)
        return result

    def _grid_coverage(
        self, model: TwinModel, stations: list[Station]
    ) -> tuple[int, int, int]:
        step = self.grid_step_km
        covered = total = overlap = 0
        # Use a representative norm (median district norm, or 600s default).
        norms = sorted(d.norm_time_s for d in model.districts.values())
        norm = norms[len(norms) // 2] if norms else 600.0
        y = 0.0
        while y <= model.area_km:
            x = 0.0
            while x <= model.area_km:
                total += 1
                responders = _responders_within(stations, model, x, y, norm)
                if responders >= 1:
                    covered += 1
                if responders >= 2:
                    overlap += 1
                x += step
            y += step
        return covered, total, overlap

    def _risk_zones(self, model: TwinModel, stations: list[Station]) -> list[str]:
        """Protected objects whose location is not covered within a strict norm."""
        zones: list[str] = []
        for obj in model.protected_objects.values():
            _, t = _nearest(stations, model, obj.x, obj.y)
            # High-risk objects demand a tighter arrival (scaled by risk class).
            strict = 600.0 - (obj.risk_class - 1) * 60.0
            if t is None or t > strict:
                zones.append(obj.id)
        return zones


@dataclass
class CoverageCell:
    x: float
    y: float
    arrival_time_s: float | None
    covered: bool


def coverage_map(
    model: TwinModel, grid_step_km: float = 3.0, norm_s: float = 600.0
) -> list[CoverageCell]:
    """A grid of cells with the nearest-station arrival time (for coverage maps)."""
    stations = model.active_stations()
    cells: list[CoverageCell] = []
    y = 0.0
    while y <= model.area_km:
        x = 0.0
        while x <= model.area_km:
            _, t = _nearest(stations, model, x, y)
            cells.append(
                CoverageCell(
                    x=round(x, 1),
                    y=round(y, 1),
                    arrival_time_s=round(t, 1) if t is not None else None,
                    covered=t is not None and t <= norm_s,
                )
            )
            x += grid_step_km
        y += grid_step_km
    return cells


def district_by_id(model: TwinModel, district_id: str) -> District | None:
    return model.districts.get(district_id)
