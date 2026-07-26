"""Analytics models.

The analytics platform is **read-only** — it introduces no persisted tables and
defines no ORM models of its own. Its "models" are the in-memory result
dataclasses in ``kpi``, ``statistics``, ``services`` and ``dashboards``. This
package is the seam for materialized-view / snapshot models in a later stage.
"""
