#!/usr/bin/env bash
# Open an interactive psql session against the running Postgres container.
#
# Reads POSTGRES_USER and POSTGRES_DB from .env if present; otherwise falls
# back to the compose defaults (vision / vision). POSTGRES_PASSWORD is
# already inside the container's environment, so the helper does not need it.
#
# Requires Docker + `docker compose` and the `postgres` service running.
#
# Usage:
#   ./scripts/psql.sh                       # interactive shell
#   ./scripts/psql.sh -c "SELECT 1"         # one-shot query
#   ./scripts/psql.sh -c "\dt"              # list tables
#   ./scripts/psql.sh -f scripts/foo.sql    # run a SQL file (file must be
#                                             reachable from inside the
#                                             container; for host paths use
#                                             redirection: psql.sh < foo.sql)

set -euo pipefail

cd "$(dirname "$0")/.."

if [ -f .env ]; then
  # shellcheck disable=SC1091
  set -a
  . ./.env
  set +a
fi

POSTGRES_USER="${POSTGRES_USER:-vision}"
POSTGRES_DB="${POSTGRES_DB:-vision}"

# `-T` keeps stdin/stdout direct so heredocs and `< file` redirections work.
exec docker compose exec -T postgres \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" "$@"
