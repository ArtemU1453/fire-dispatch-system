"""Administration platform — users, RBAC, settings, directories, integrations.

A single administrative module for managing users, roles and permissions,
system settings, catalogs (directories), integrations and operational
parameters, plus audit-log views. It contains **no dispatch business logic** and
**does not modify** any existing business module — it operates through the
existing models and services.
"""
