#!/usr/bin/env bash
# project-agent-system — fresh-VPS install script.
#
# Brings up the full Compose stack from a clean clone. Idempotent — safe
# to re-run after partial installs, network hiccups, or reboot. Fails fast
# on missing prerequisites with explicit remediation messages.
#
# Per REQ-PORT-vps-deploy: must complete to a passing smoke test in under
# 60 minutes on the reference VPS spec (4 vCPU / 8 GB RAM / ≥50 GB disk
# running Ubuntu 22.04 / 24.04 or Debian 12 with Docker Engine ≥24 and
# Docker Compose v2). No host-specific patches, no interactive prompts
# beyond `.env`. Smoke testing is invoked separately via
# `scripts/smoke_test.sh` (lands with TASK-smoke-test-skeleton).
#
# Per CON-local-first-inference: default deployment makes zero remote
# inference calls. Operator must explicitly opt into a remote-inference
# profile via `.env` later.
#
# Per ASM-vps-docker-baseline-stable: assumes the Docker-capable-VPS
# baseline is already present. This script does NOT install Docker or
# Compose — it verifies their presence and instructs the operator if
# either is missing.
#
# Usage:
#   bash scripts/install_vps.sh
#
# Exit codes:
#   0  — install completed; all expected services healthy.
#   1  — prerequisite missing (Docker, Compose v2, .env, or required keys).
#   2  — drift detected between .env.example and docker-compose.yml.
#   3  — Compose up succeeded but ≥1 service did not become healthy
#        within the deadline. Stack is left running for inspection.

set -euo pipefail

cd "$(dirname "$0")/.."
REPO_ROOT="$(pwd)"

HEALTHCHECK_DEADLINE_SECS=300  # 5 minutes; uvicorn boot + Postgres init typically <60s
HEALTHCHECK_POLL_SECS=5

# ANSI color helpers (no-op if stdout is not a tty).
if [ -t 1 ]; then
    BOLD=$(printf '\033[1m')
    GREEN=$(printf '\033[32m')
    RED=$(printf '\033[31m')
    YELLOW=$(printf '\033[33m')
    RESET=$(printf '\033[0m')
else
    BOLD=""; GREEN=""; RED=""; YELLOW=""; RESET=""
fi

log()  { printf "%s==>%s %s\n" "${BOLD}" "${RESET}" "$*"; }
ok()   { printf "%s✓%s   %s\n" "${GREEN}" "${RESET}" "$*"; }
warn() { printf "%s⚠%s   %s\n" "${YELLOW}" "${RESET}" "$*" >&2; }
err()  { printf "%s✗%s   %s\n" "${RED}"   "${RESET}" "$*" >&2; }

# === Step 1: prerequisites ============================================
log "Verifying prerequisites..."

if ! command -v docker > /dev/null 2>&1; then
    err "Docker is required but not found."
    err "  Install Docker Engine ≥ 24:   https://docs.docker.com/engine/install/"
    err "  Then re-run this script."
    exit 1
fi
ok "Docker available: $(docker --version)"

if ! docker compose version > /dev/null 2>&1; then
    err "Docker Compose v2 is required (the 'docker compose' subcommand, not 'docker-compose')."
    err "  Modern Docker Engine includes the Compose v2 plugin."
    err "  If you have only the legacy 'docker-compose' binary, install the v2 plugin:"
    err "    https://docs.docker.com/compose/install/linux/"
    exit 1
fi
ok "Compose available: $(docker compose version --short 2>/dev/null || docker compose version)"

if [ ! -f "$REPO_ROOT/docker-compose.yml" ]; then
    err "docker-compose.yml not found in $REPO_ROOT."
    err "  Run this script from the project repo root (or via 'bash scripts/install_vps.sh')."
    exit 1
fi
ok "Repo root: $REPO_ROOT"

# === Step 2: .env exists ==============================================
log "Verifying .env configuration..."

if [ ! -f "$REPO_ROOT/.env" ]; then
    err ".env not found."
    err "  Copy the template and fill in real values:"
    err "    cp .env.example .env"
    err "    \$EDITOR .env"
    err "  Generate auth tokens with:   openssl rand -hex 32"
    exit 1
fi
ok ".env present"

# === Step 3: drift check ==============================================
log "Checking .env.example ↔ docker-compose.yml alignment..."

if ! bash "$REPO_ROOT/scripts/check-env-drift.sh"; then
    err "Drift detected between .env.example and docker-compose.yml (see above)."
    err "  Fix the drift before installing — either add the missing keys to"
    err "  .env.example or remove unreferenced ones."
    exit 2
fi

# === Step 4: required-key value check =================================
log "Verifying required .env keys are non-empty..."

# Source .env into the current shell so we can introspect values.
# `set -a` exports each assignment; `set +a` reverts. We silence the
# 'unbound variable' option just for the dot-source so set -u doesn't trip
# on a malformed .env.
set -a
# shellcheck disable=SC1091
. "$REPO_ROOT/.env"
set +a

REQUIRED_KEYS=(
    COMPOSE_PROFILES
    POSTGRES_PASSWORD
    WHATSORGA_INGEST_TOKEN
    HERMES_RUNTIME_TOKEN
    BACKLOG_CORE_TOKEN
    GBRAIN_BRIDGE_TOKEN
    KANBAN_SYNC_TOKEN
    OPERATOR_TOKEN
)
missing_keys=()
for key in "${REQUIRED_KEYS[@]}"; do
    if [ -z "${!key:-}" ]; then
        missing_keys+=("$key")
    fi
done

if [ ${#missing_keys[@]} -gt 0 ]; then
    err "Required .env keys are empty: ${missing_keys[*]}"
    err "  Generate auth tokens with:   openssl rand -hex 32"
    err "  Then re-run this script."
    exit 1
fi
ok "All ${#REQUIRED_KEYS[@]} required .env keys are non-empty"

# Profile-specific check: tailscale needs TS_AUTHKEY.
if [[ "${COMPOSE_PROFILES}" == *"tailscale"* ]] && [ -z "${TS_AUTHKEY:-}" ]; then
    err "COMPOSE_PROFILES contains 'tailscale' but TS_AUTHKEY is empty."
    err "  Get an auth key from https://login.tailscale.com/admin/settings/keys"
    err "  and set TS_AUTHKEY in .env."
    exit 1
fi

log "Active Compose profiles: ${COMPOSE_PROFILES}"

# === Step 5: pull images ==============================================
log "Pulling Compose images (this is the slowest step on a fresh host)..."
docker compose pull

# === Step 6: build local components ===================================
log "Building per-component images (whatsorga-ingest, hermes-runtime, ...) ..."
docker compose build

# === Step 7: bring up the stack =======================================
log "Starting the stack (docker compose up -d)..."
docker compose up -d

# === Step 8: wait for healthchecks ====================================
log "Waiting for services to report healthy (deadline: ${HEALTHCHECK_DEADLINE_SECS}s)..."

# Containers we expect to have a healthcheck and become healthy.
# Tailscale ingress has no healthcheck (its own daemon manages liveness),
# so we exclude it here.
EXPECTED_HEALTHY=(
    project-agent-system-postgres
    project-agent-system-ollama
    project-agent-system-backlog-core
    project-agent-system-whatsorga-ingest
    project-agent-system-hermes-runtime
    project-agent-system-gbrain-bridge
    project-agent-system-kanban-sync
)

container_health() {
    local container="$1"
    docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "missing"
}

deadline=$(($(date +%s) + HEALTHCHECK_DEADLINE_SECS))
all_healthy=false
last_status_line=""

while [ "$(date +%s)" -lt "$deadline" ]; do
    healthy_count=0
    pending=()
    for c in "${EXPECTED_HEALTHY[@]}"; do
        s=$(container_health "$c")
        if [ "$s" = "healthy" ]; then
            healthy_count=$((healthy_count + 1))
        else
            pending+=("$c=${s}")
        fi
    done

    status_line="  ${healthy_count}/${#EXPECTED_HEALTHY[@]} healthy"
    if [ "${#pending[@]}" -gt 0 ]; then
        status_line+=" • pending: ${pending[*]}"
    fi
    if [ "$status_line" != "$last_status_line" ]; then
        printf "%s\n" "$status_line"
        last_status_line="$status_line"
    fi

    if [ "$healthy_count" -eq "${#EXPECTED_HEALTHY[@]}" ]; then
        all_healthy=true
        break
    fi
    sleep "$HEALTHCHECK_POLL_SECS"
done

if [ "$all_healthy" != true ]; then
    warn "Not all services became healthy within ${HEALTHCHECK_DEADLINE_SECS}s."
    warn "  Inspect status:    docker compose ps"
    warn "  Tail logs:         docker compose logs --tail=200 -f"
    warn "  The stack is left running so you can investigate."
    exit 3
fi
ok "All ${#EXPECTED_HEALTHY[@]} expected services are healthy"

# === Step 9: pull Ollama model ========================================
log "Pulling Ollama model (${OLLAMA_MODEL:-gemma3:4b})..."
bash "$REPO_ROOT/scripts/ollama-pull.sh"
ok "Ollama model ready"

# === Step 10: report next steps =======================================
cat <<NEXT_STEPS

${BOLD}${GREEN}✓ Install complete.${RESET}

Default deployment makes zero remote inference calls (per CON-local-
first-inference). To verify the stack:

  ${BOLD}1. Quick health check from inside the stack:${RESET}
     docker compose --profile cli run --rm cli health

  ${BOLD}2. Or install the operator CLI on this host:${RESET}
     uv tool install --from ./3-code/cli vision-cli
     vision health

  ${BOLD}3. Run the smoke test (when smoke_test.sh lands per TASK-smoke-test-skeleton):${RESET}
     bash scripts/smoke_test.sh

Operational references:
  • ${BOLD}docker compose ps${RESET}              service status
  • ${BOLD}docker compose logs <service>${RESET}  per-service logs
  • ${BOLD}.env${RESET}                            runtime config (rotate per REQ-REL-secret-rotation)
  • ${BOLD}4-deploy/runbooks/${RESET}              operational procedures (lands with phase-1 manual testing)

Phase 1 milestone: stack is up. Continue with TASK-phase-1-manual-testing.

NEXT_STEPS
