"""Administration validators.

Domain validation lives close to where it is used: password rules in
``utils.passwords`` (validated by ``UserService``), typed-value parsing in
``services.settings_service``, and directory field whitelisting in
``services.directory_service``. This package is the seam for shared validators.
"""
