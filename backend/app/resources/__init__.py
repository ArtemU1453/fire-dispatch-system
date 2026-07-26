"""Real-time resource / unit management.

Keeps the live state of units, vehicles, crews and personnel, manages statuses
(the shared availability catalog), crews and incident assignments, and records an
append-only history. It builds on the Stage-2 resource model without modifying
it; status changes update the ``resources.availability_status`` the Dispatch
Engine already reads, so the engine always uses current data.
"""
