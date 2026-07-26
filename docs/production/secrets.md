# Secrets Management (§2)

How the AI Dispatcher МЧС system stores and resolves sensitive values —
passwords, API keys, TLS certificates, access tokens and encryption keys —
**without ever committing them to the repository**.

## Principles

1. **No secrets in the repository or in source code.** The repo contains only
   *templates* (`.env.example`, `deploy/env/*.example`) with placeholders. Real
   values are supplied at runtime.
2. **Resolved through an abstraction.** The application reads secrets through
   `app.config.secrets.SecretsProvider`, chosen by `SECRETS_PROVIDER`. Call
   sites never know where a secret physically lives.
3. **Right source per environment.** Development uses environment variables;
   containers use mounted secret files; production uses mounted files or a
   corporate secrets manager.
4. **Not in backups or logs.** File backups exclude `.env`/`*.key`/`*.pem`; logs
   and metrics mask sensitive keys (see the security audit and masking policy).

## Providers

| `SECRETS_PROVIDER` | Class | Source | Use |
|--------------------|-------|--------|-----|
| `env` (default) | `EnvSecretsProvider` | environment variables (optional `SECRETS_ENV_PREFIX`) | development, CI |
| `file` | `FileSecretsProvider` | one file per key under `SECRETS_DIR` (default `/run/secrets`) | containers/Kubernetes/Swarm, production |
| `vault` | `VaultSecretsProvider` | corporate secrets manager (seam) | production with a vault |

```python
from app.config.secrets import get_secrets_provider

secrets = get_secrets_provider()
db_password = secrets.get_required("POSTGRES_PASSWORD")   # raises if absent
api_key = secrets.get("SOME_API_KEY", default=None)       # optional
```

### env provider

Reads from process environment, optionally with a prefix so a corporate naming
convention (`DISPATCHER_POSTGRES_PASSWORD`) backs the logical key
(`POSTGRES_PASSWORD`). Suitable for development and CI where values are
throwaway. **Not** recommended for production (env is visible to child processes
and some tooling).

### file provider (recommended for containers)

Each secret is a file named after its key: `/run/secrets/POSTGRES_PASSWORD`,
`/run/secrets/SOME_API_KEY`. The value is the file's trimmed content. This maps
directly to:

- **Docker Compose / Swarm** `secrets:` (mounted at `/run/secrets/<name>`),
- **Kubernetes** `Secret` projected as a volume,
- **systemd** credentials (`$CREDENTIALS_DIRECTORY`).

Path-traversal is refused (only bare key names are honoured).

### vault provider (corporate secrets manager — seam)

The integration **contract** is implemented; no live vault client is bundled
(no real vault is provisioned in this stage). Connection settings come from
config (`VAULT_ADDR`, `VAULT_NAMESPACE`, `VAULT_KV_MOUNT`, `VAULT_SECRET_PATH`).
To go live, an operator installs their vendor SDK (e.g. `hvac`) and injects a
client implementing `read_secret(path, key) -> str | None`:

```python
from app.config.secrets import set_vault_client
set_vault_client(my_hvac_backed_client)   # at process startup; no call-site change
```

Until a client is set, the vault provider **fails closed** (raises), so a
misconfiguration can never be mistaken for "no secret configured".

## What is a secret (and where it goes)

| Secret | Key (example) | Source in production |
|--------|---------------|----------------------|
| Database password | `POSTGRES_PASSWORD` | file / vault |
| GIS provider API keys/tokens | `GIS_PELIAS_API_KEY`, `GIS_ARCGIS_TOKEN` | file / vault |
| Integration credentials (telephony, gov systems) | per integration | file / vault |
| TLS certificates / private keys | mounted files | orchestrator secret / cert-manager |
| Encryption keys | `*_ENCRYPTION_KEY` | file / vault |

Non-secret configuration (hosts, ports, feature flags, pool sizes) stays in the
normal environment / config — see [configuration.md](configuration.md).

## Operational practices

- **Rotation** — rotate on a schedule and on suspected compromise. With `file`,
  update the mounted secret and restart/roll the instances (stateless, safe).
  With a vault, prefer short-lived dynamic credentials / leases.
- **Least privilege** — the database role, API tokens and integration accounts
  get only the permissions they need.
- **Separation** — each environment has its own secrets; never share production
  secrets with staging/testing.
- **Auditing** — secret *access* is auditable at the vault; secret *values* are
  never logged (masking policy).
- **Incident response** — on leak: rotate the affected secret, invalidate old
  credentials, review `audit_logs`.

## Verifying

- `git grep -nE '(password|secret|token|api_key)\s*=\s*["'\'']` should show only
  templates/tests, never real values.
- Start one instance with the target `SECRETS_PROVIDER` and confirm required
  keys resolve (a missing required secret raises `SecretNotFoundError` at use).
- `tests/config/test_secrets.py` covers the env/file/vault providers.
