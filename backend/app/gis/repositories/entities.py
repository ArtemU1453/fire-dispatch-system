"""Concrete repositories for the GIS models.

Thin subclasses of the Stage-2 generic :class:`SqlAlchemyRepository`, inheriting
CRUD + filter/sort/paginate + soft-delete (DRY).
"""

from __future__ import annotations

from app.gis.models import (
    Address,
    Building,
    Coordinate,
    District,
    GeocodingLog,
    Region,
    Settlement,
    Street,
)
from app.repositories.base import SqlAlchemyRepository


class RegionRepository(SqlAlchemyRepository[Region]):
    model = Region


class DistrictRepository(SqlAlchemyRepository[District]):
    model = District


class SettlementRepository(SqlAlchemyRepository[Settlement]):
    model = Settlement


class StreetRepository(SqlAlchemyRepository[Street]):
    model = Street


class BuildingRepository(SqlAlchemyRepository[Building]):
    model = Building


class CoordinateRepository(SqlAlchemyRepository[Coordinate]):
    model = Coordinate


class AddressRepository(SqlAlchemyRepository[Address]):
    model = Address


class GeocodingLogRepository(SqlAlchemyRepository[GeocodingLog]):
    model = GeocodingLog
