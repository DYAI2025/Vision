#!/usr/bin/env bash
# .env.example drift check.
#
# Verifies that:
#   1. Every ${VAR} reference in docker-compose.yml is declared in .env.example.
#   2. Every key declared in .env.example is referenced in docker-compose.yml,
#      with the exception of Compose-intrinsic vars (e.g. COMPOSE_PROFILES) which
#      Compose reads directly without ${...} substitution.
#
# Per REQ-MNT-env-driven-config — run by CI on every PR via
# .github/workflows/ci.yml. Operators may also run it locally.
#
# Exit codes:
#   0 — clean (no missing, no unexpected orphans)
#   1 — drift detected (missing keys or unrecognized orphans)

set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f docker-compose.yml ]; then
  echo "ERROR: docker-compose.yml not found in $(pwd)" >&2
  exit 1
fi

if [ ! -f .env.example ]; then
  echo "ERROR: .env.example not found in $(pwd)" >&2
  exit 1
fi

# Compose ${VAR}, ${VAR:-default}, ${VAR:?error}, ${VAR-default}, ${VAR?error}.
COMPOSE_KEYS=$(grep -oE '\$\{[A-Z][A-Z0-9_]+' docker-compose.yml | sed 's/^\${//' | sort -u)

# .env.example keys (lines like KEY=...; ignores comments and blanks).
ENV_EXAMPLE_KEYS=$(grep -E '^[A-Z][A-Z0-9_]+=' .env.example | cut -d= -f1 | sort -u)

# Compose intrinsics — env vars Compose reads directly, not via ${...} in YAML.
INTRINSIC='^(COMPOSE_PROFILES|COMPOSE_FILE|COMPOSE_PROJECT_NAME|COMPOSE_PATH_SEPARATOR|COMPOSE_DOCKER_CLI_BUILD|DOCKER_DEFAULT_PLATFORM)$'

# Missing: referenced in compose but not declared in .env.example.
MISSING=$(comm -23 <(echo "$COMPOSE_KEYS") <(echo "$ENV_EXAMPLE_KEYS") || true)

# Orphan: declared in .env.example but not referenced in compose, excluding intrinsics.
ORPHAN=$(comm -13 <(echo "$COMPOSE_KEYS") <(echo "$ENV_EXAMPLE_KEYS") | grep -vE "$INTRINSIC" || true)

EXIT_CODE=0

if [ -n "$MISSING" ]; then
  echo "ERROR: keys referenced in docker-compose.yml but missing from .env.example:" >&2
  # shellcheck disable=SC2001 # sed is more idiomatic here than ${var//$'\n'/$'\n'  }
  echo "$MISSING" | sed 's/^/  /' >&2
  EXIT_CODE=1
fi

if [ -n "$ORPHAN" ]; then
  echo "ERROR: keys in .env.example not referenced in docker-compose.yml (and not Compose intrinsics):" >&2
  # shellcheck disable=SC2001 # sed is more idiomatic here than ${var//$'\n'/$'\n'  }
  echo "$ORPHAN" | sed 's/^/  /' >&2
  echo "  (If a key is intentionally for a service not yet wired into Compose," >&2
  echo "   either wire it in the relevant service's environment block or remove" >&2
  echo "   it from .env.example until the service skeleton task lands.)" >&2
  EXIT_CODE=1
fi

if [ $EXIT_CODE -eq 0 ]; then
  COUNT=$(echo "$COMPOSE_KEYS" | wc -l | tr -d ' ')
  echo "OK: .env.example matches docker-compose.yml exactly (${COUNT} keys checked)."
fi

exit $EXIT_CODE
