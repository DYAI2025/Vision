#!/usr/bin/env bash
# Pull the configured Ollama model into the running container.
#
# Reads OLLAMA_MODEL from .env if present (defaults to gemma3:4b — see
# .env.example and 4-deploy/ollama/README.md). Idempotent: re-running
# pulls only updated layers.
#
# Run once after `docker compose up` on a fresh deployment, or after
# changing OLLAMA_MODEL in .env. `TASK-install-vps-script` will fold
# this into the install runbook so a fresh-VPS install is one command.
#
# Requires Docker + `docker compose` and the `ollama` service running.

set -euo pipefail

cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091  # .env is operator-supplied, not present at lint time
  . ./.env
  set +a
fi

OLLAMA_MODEL="${OLLAMA_MODEL:-gemma3:4b}"

echo "Pulling Ollama model: $OLLAMA_MODEL ..."
exec docker compose exec -T ollama ollama pull "$OLLAMA_MODEL"
