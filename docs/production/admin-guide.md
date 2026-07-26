# Administrator Guide (§12)

For operators who administer the AI Dispatcher МЧС system: users, roles,
settings, integrations, and day-to-day operations. Detailed module behaviour is
in [../admin.md](../admin.md); this guide is task-oriented.

## Responsibilities

- Manage **users, roles and permissions** (RBAC).
- Manage **system settings** (versioned, with history).
- Register and monitor **integrations** (telephony, GIS, directories, gov systems).
- Oversee **backups, upgrades, monitoring** and **security**.

## Access control (RBAC)

- Permissions are granted **through roles**; users hold one or more roles.
- Custom roles and permissions can be created in the database/admin module.
- `is_superuser` bypasses checks — grant sparingly.
- Analytics/exports are gated (`analytics.view`, `analytics.export`,
  `analytics.admin`).
- **Before external exposure**, ensure an authentication layer fronts the API
  (security audit R1) so RBAC actually gates requests.

Typical tasks: create a dispatcher role with the operational permissions; assign
users; review effective permissions.

## Settings

- Settings are centralised and **versioned** — every change is recorded with
  history, and secret-like values are masked in history.
- Prefer changing operational policy (e.g. dispatch rules) via settings rather
  than code. Roll back to a previous version if a change misbehaves.

## Integrations

- Each external system is a registered integration with typed configuration.
- Credentials come from the **secrets manager**, never stored in the repo
  ([secrets.md](secrets.md)).
- Monitor integration health via the Observability health providers.

## Operational duties

- **Backups** — confirm daily success; run restore drills ([backup.md](backup.md),
  [recovery.md](recovery.md)).
- **Monitoring** — watch dashboards for error-rate/latency; investigate via Trace
  IDs; review `audit_logs` weekly.
- **Upgrades** — follow [upgrade.md](upgrade.md); back up first.
- **Security** — keep `DEBUG=false`, CORS restricted, TLS enforced, secrets
  rotated (security audit checklist).

## Audit

Administrative actions and analytics exports are written to an immutable
`audit_logs` trail (who/what/when). Use it for accountability and incident
review.
