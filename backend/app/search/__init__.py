"""Universal resource search engine.

Searches the core ``Resource`` entity with fully composable filters, PostGIS
spatial operations, sorting and pagination — working identically for any resource
kind (station, vehicle, hydrant, hospital, police, …). Built on the Stage-2 models
and the Stage-3 GIS module without changing them.

Ranking/selection is deliberately out of scope: a ``SelectionStrategy`` seam lets
the next stage add automatic unit selection without modifying the engine.
"""
