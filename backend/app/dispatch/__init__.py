"""Automatic dispatch recommendation module.

Given an incident (address/coordinates + type + complexity), forms a recommended
composition of forces and equipment for the dispatcher — using the Stage-2 data
model, Stage-3 GIS and the Stage-4 Search Engine, without changing them.

The module is **advisory only**: it never dispatches units, builds routes,
computes ETA, or talks to external systems. Rules live outside the code (YAML)
and a routing/ETA estimator can be plugged into scoring later without rework.
"""
