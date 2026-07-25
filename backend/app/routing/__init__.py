"""Routing & ETA module.

An independent module providing a single :class:`RoutingProvider` seam over any
routing backend, with services for building routes, distances and ETA. The
Dispatch Engine obtains arrival times through this module's ``ETAService``.
"""
