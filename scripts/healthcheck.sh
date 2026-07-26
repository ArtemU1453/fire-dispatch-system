#!/usr/bin/env bash
# =========================================================================
# Standalone container/instance readiness probe (Stage 16 §6).
# Exit 0 when the instance is live and (optionally) the database is up.
#
# Usage:
#   scripts/healthcheck.sh                 # liveness: process serves /health
#   READINESS=1 scripts/healthcheck.sh     # readiness: also require database=up
# Env: HEALTH_URL (default http://127.0.0.1:8000/health)
# =========================================================================
set -euo pipefail
URL="${HEALTH_URL:-http://127.0.0.1:8000/health}"
READINESS="${READINESS:-0}"

python - "$URL" "$READINESS" <<'PY'
import json, sys, urllib.request

url, readiness = sys.argv[1], sys.argv[2] == "1"
try:
    with urllib.request.urlopen(url, timeout=4) as r:
        if r.status != 200:
            print(f"unhealthy: HTTP {r.status}", file=sys.stderr)
            sys.exit(1)
        body = json.loads(r.read() or b"{}")
except Exception as exc:  # noqa: BLE001
    print(f"unhealthy: {exc}", file=sys.stderr)
    sys.exit(1)

if readiness and body.get("database") != "up":
    print(f"not ready: database={body.get('database')}", file=sys.stderr)
    sys.exit(1)
print(f"ok: status={body.get('status')} database={body.get('database')}")
PY
