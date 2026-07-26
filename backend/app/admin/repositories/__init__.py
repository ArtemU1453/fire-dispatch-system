"""Administration repositories.

Persistence for the admin module is encapsulated inside the services (each owns
its eager-loading queries against the reused and new tables). This package is the
seam for extracting dedicated repository classes should the queries grow.
"""
