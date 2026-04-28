#!/usr/bin/env bash
# Run an `ollama` command inside the running ollama container.
#
# Requires Docker + `docker compose` and the `ollama` service running.
#
# Usage:
#   ./scripts/ollama.sh list                    # list pulled models
#   ./scripts/ollama.sh ps                      # currently loaded models
#   ./scripts/ollama.sh run gemma3:4b "hello"   # one-shot generation
#   ./scripts/ollama.sh pull gemma3:1b          # pull a specific model
#   ./scripts/ollama.sh rm gemma2:2b            # remove an unused model
#
# See 4-deploy/ollama/README.md for the full model selection guide.

set -euo pipefail

cd "$(dirname "$0")/.."

# `-T` keeps stdin/stdout direct so streaming generation output is unbuffered.
exec docker compose exec -T ollama ollama "$@"
