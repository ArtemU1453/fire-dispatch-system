"""GIS geospatial core.

An independent, extensible module providing geocoding, reverse geocoding, address
normalization and PostGIS spatial queries. It depends on the Stage-1/2 foundation
(config, database, ORM base) but adds no coupling back into them, so it can evolve
on its own. Business logic (dispatch, nearest-resource search, routing) is
deliberately out of scope.
"""
