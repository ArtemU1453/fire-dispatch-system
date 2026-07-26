"""Observability repositories.

Observability data (metrics, traces, logs, alerts) is kept in-process by the
``state`` singletons and read via the collectors / services; business gauges are
read straight from existing tables by the collectors. This package is the seam for
a persistent store (e.g. exporting to a time-series DB) in a later stage.
"""
