"""Mobile platform BFF (Stage 19).

Backend-for-frontend for the two mobile apps — **Commander** (command staff) and
**Responder** (units). All decisions and aggregation happen here on the server;
the mobile apps are thin clients that only render what these endpoints return and
send user actions back. Includes an abstract, vendor-neutral PushService, a
secure token/session abstraction, and offline-sync support.
"""
