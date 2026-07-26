#!/usr/bin/env bash
# =========================================================================
# Automated production-readiness checks (Stage 16 §13).
# Runs the machine-checkable parts of the readiness checklist and prints a
# pass/fail summary. Human-judgement items remain in docs/readiness-checklist.md.
#
# Usage: scripts/verify/verify_readiness.sh
#   Set RUN_DB=0 to skip database-dependent checks (migrations).
# =========================================================================
set -uo pipefail
cd "$(cd "$(dirname "$0")/../.." && pwd)"

PASS=0 FAIL=0
check() {  # check "name" command...
  local name="$1"; shift
  if "$@" >/tmp/_vr.$$ 2>&1; then
    printf '  PASS  %s\n' "$name"; PASS=$((PASS+1))
  else
    printf '  FAIL  %s\n' "$name"; FAIL=$((FAIL+1)); sed 's/^/        /' /tmp/_vr.$$ | tail -5
  fi
  rm -f /tmp/_vr.$$
}

echo "== Static analysis =="
check "ruff (backend, tests)" ruff check backend tests

echo "== Tests =="
check "pytest suite" python -m pytest -q

echo "== Secrets hygiene =="
# No real-looking assignments outside templates/tests/docs.
check "no hard-coded secrets" bash -c '
  ! git grep -nEI "(password|secret|token|api_key)[[:space:]]*[:=][[:space:]]*[\"'\''][^\"'\'' ]{6,}" -- \
    ":!*.example" ":!*.md" ":!tests/*" ":!docs/*" ":!*.lock" | grep -vE "example|changeme|your-|<|placeholder" '

echo "== Container =="
check "Dockerfile present" test -f Dockerfile
check "compose config valid" bash -c 'command -v docker >/dev/null && docker compose config >/dev/null || echo "docker not present (skipped)"'

if [ "${RUN_DB:-1}" = "1" ]; then
  echo "== Migrations (requires database) =="
  check "migrations round-trip + no drift" bash scripts/verify/check_migrations.sh
else
  echo "== Migrations: skipped (RUN_DB=0) =="
fi

echo
echo "Summary: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
