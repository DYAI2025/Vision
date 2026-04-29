#!/usr/bin/env bash
# project-agent-system — Phase-1 healthcheck-only smoke test.
#
# Phase-1 acceptance per the Execution Plan in 3-code/tasks.md:
#   "Fresh-VPS install completes from clean clone to passing
#    healthcheck-only smoke test."
#
# What this script does (Phase 1 scope):
#   1. Verifies all 7 expected Compose containers report "healthy"
#      (postgres, ollama, 5 backend services).
#   2. Invokes `vision health` via the cli Compose service to confirm
#      the aggregator agrees and overall status is "ok". Propagates
#      vision's exit code.
#
# What this script does NOT yet do (deferred to Phase-7
# TASK-cross-provider-verification, which extends this script with the
# full REQ-PORT-vps-deploy functional flow):
#   - Synthetic ingest on each of the 4 MVP channels
#   - Routing decision + cited_pages assertion
#   - Autonomous-band Kanban card creation via proposal pipeline
#   - Mid-band review-queue assertion
#   - RTBF cascade end-to-end with verification query
#   - processing.stuck audit-log assertion
# These checks require Phase 2-7 functionality (proposal pipeline,
# routing skill, RTBF cascade engine, etc.) and will be folded into
# this script as those tasks land. The exit-code contract below is
# stable across that evolution.
#
# Caddy-mode-only at Phase 1 — the cli Compose service hits
# `http://ingress-caddy/v1/health/<service>` per the Caddy aggregation
# pattern. Tailscale-mode operators must run `vision health` directly
# from a tailnet-connected host with VISION_BASE_URL pointed at the
# Tailnet hostname (per `app/health.py` docstring + DEC-cursor-
# pagination-and-event-stream-conventions / api-design.md notes).
#
# Per CON-local-first-inference: invokes only local services. Records
# zero remote inference calls in the audit log.
#
# Usage:
#   bash scripts/smoke_test.sh
#
# Prerequisites:
#   - Stack already running. Run scripts/install_vps.sh first if not.
#
# Exit codes:
#   0  — all containers healthy + vision health returned "ok".
#   1  — prerequisite missing (no Compose stack, .env unreadable).
#   2  — one or more containers not Compose-healthy.
#   3  — vision health reported "degraded" (aggregator's exit code 1).
#   4  — vision health reported "down" (aggregator's exit code 2).
#   5  — non-caddy COMPOSE_PROFILES; smoke test does not apply.

set -euo pipefail

cd "$(dirname "$0")/.."
REPO_ROOT="$(pwd)"

# ANSI color helpers (no-op if stdout is not a tty). Same shape as
# install_vps.sh.
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
log "Phase-1 healthcheck-only smoke test"

if [ ! -f "$REPO_ROOT/docker-compose.yml" ]; then
    err "docker-compose.yml not found in $REPO_ROOT."
    err "  Run from the repo root (or via 'bash scripts/smoke_test.sh')."
    exit 1
fi

if ! command -v docker > /dev/null 2>&1 || ! docker compose version > /dev/null 2>&1; then
    err "Docker + Compose v2 required but not available."
    err "  Run scripts/install_vps.sh first to verify the prerequisite stack."
    exit 1
fi

if [ ! -f "$REPO_ROOT/.env" ]; then
    err ".env not found. Run scripts/install_vps.sh first."
    exit 1
fi

# Source .env for COMPOSE_PROFILES.
set -a
# shellcheck disable=SC1091  # .env is operator-supplied, not present at lint time
. "$REPO_ROOT/.env"
set +a

# === Step 2: profile gate =============================================
# Phase 1 supports caddy-mode only. Tailscale mode is documented as a
# deferred-hardening item (the cli's caddy-aggregation pattern doesn't
# work over `tailscale serve` since it has no URL-rewrite support).
if [[ "${COMPOSE_PROFILES:-}" != *"caddy"* ]]; then
    warn "COMPOSE_PROFILES=${COMPOSE_PROFILES:-<unset>}; this smoke test"
    warn "supports only caddy mode at Phase 1."
    warn ""
    warn "For tailscale mode, run vision health directly from a tailnet-"
    warn "connected host:"
    warn "    VISION_BASE_URL=https://<TS_HOSTNAME>.<tailnet>.ts.net vision health"
    warn ""
    warn "Exiting 5 (not-applicable) to preserve Phase-7 cross-provider"
    warn "verification clarity (a true failure exits 2/3/4)."
    exit 5
fi
ok "Active profile: ${COMPOSE_PROFILES}"

# === Step 3: container-level health ===================================
log "Checking Compose container health status..."

EXPECTED_HEALTHY=(
    project-agent-system-postgres
    project-agent-system-ollama
    project-agent-system-backlog-core
    project-agent-system-whatsorga-ingest
    project-agent-system-hermes-runtime
    project-agent-system-gbrain-bridge
    project-agent-system-kanban-sync
)
unhealthy=()
for c in "${EXPECTED_HEALTHY[@]}"; do
    s=$(docker inspect --format='{{.State.Health.Status}}' "$c" 2>/dev/null || echo "missing")
    if [ "$s" = "healthy" ]; then
        ok "$c"
    else
        unhealthy+=("$c=${s}")
        err "$c (status=${s})"
    fi
done

if [ ${#unhealthy[@]} -gt 0 ]; then
    err ""
    err "Containers not healthy: ${#unhealthy[@]} of ${#EXPECTED_HEALTHY[@]}"
    err "  Inspect:    docker compose ps"
    err "  Logs:       docker compose logs --tail=200 -f"
    exit 2
fi
ok "All ${#EXPECTED_HEALTHY[@]} containers Compose-healthy"

# === Step 4: aggregated health via vision CLI =========================
log "Running vision health aggregator (via cli Compose service)..."

# `--profile cli run --rm` builds the cli image on first run; subsequent
# runs reuse the cache. `vision health` exits 0/1/2 for ok/degraded/down;
# we map those to our 0/3/4 exit codes for clarity in CI logs.
set +e
docker compose --profile cli run --rm cli health
vision_exit=$?
set -e

case "$vision_exit" in
    0)
        ok "vision health: overall=ok"
        ;;
    1)
        err "vision health: overall=degraded"
        err "  At least one service reports status: degraded."
        err "  Inspect docker compose logs for the affected service."
        exit 3
        ;;
    2)
        err "vision health: overall=down"
        err "  At least one service is unreachable or reports status: down."
        err "  This is more severe than 'degraded' — inspect immediately."
        exit 4
        ;;
    *)
        err "vision health: unexpected exit code $vision_exit"
        err "  Treating as 'down'."
        exit 4
        ;;
esac

# === Done =============================================================
cat <<DONE

${BOLD}${GREEN}✓ Phase-1 smoke test passed.${RESET}

  Containers healthy: ${#EXPECTED_HEALTHY[@]}/${#EXPECTED_HEALTHY[@]}
  vision health:      ok

This Phase-1 smoke is healthcheck-only. The full functional smoke per
REQ-PORT-vps-deploy (synthetic ingest, routing, Kanban write, RTBF
cascade) lands in TASK-cross-provider-verification (Phase 7) once the
required functionality is in place. The exit-code contract above is
stable across that evolution — automation that gates on this script
does not need to change when the functional flow extends it.

DONE
