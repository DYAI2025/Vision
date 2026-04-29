# Runbook: Fresh-VPS install

**Phase 1 deliverable.** Brings up the full `project-agent-system` Compose stack from a clean repo clone on a Docker-capable Linux VPS. Phase-1 verification is **healthcheck-only**; the full functional smoke (synthetic ingest → routing → Kanban → mid-band review → RTBF cascade) per `REQ-PORT-vps-deploy` lands when `TASK-cross-provider-verification` (Phase 7) extends `scripts/smoke_test.sh`.

**Active decisions referenced by this runbook:**
- [`DEC-gdpr-legal-review-deferred`](../../decisions/DEC-gdpr-legal-review-deferred.md) — production deploy is **blocked** until `ASM-derived-artifacts-gdpr-permissible.Status == Verified`. This runbook is for development / personal-use deploys only.
- [`DEC-postgres-as-event-store`](../../decisions/DEC-postgres-as-event-store.md) — Postgres as a Compose service.
- [`DEC-backend-stack-python-fastapi`](../../decisions/DEC-backend-stack-python-fastapi.md) + [`DEC-cli-stack-python-typer`](../../decisions/DEC-cli-stack-python-typer.md) — operator-facing tools all run on Python 3.12 + uv.

---

## Overview

A fresh install brings up:
- 5 backend HTTP services on an internal Docker bridge: `whatsorga-ingest`, `hermes-runtime`, `backlog-core`, `gbrain-bridge`, `kanban-sync`.
- 2 storage layers: Postgres 16 (event store), Ollama (local Gemma model).
- 1 ingress profile: `caddy` (default) or `tailscale`.
- 1 optional CLI service for in-stack operator commands.

**Default deployment makes zero remote inference calls** per [`CON-local-first-inference`](../../1-spec/constraints/CON-local-first-inference.md). Operator must explicitly opt into a remote-inference profile via `.env` later.

**Target time-to-first-success:** under 60 minutes on the reference VPS spec per [`REQ-PORT-vps-deploy`](../../1-spec/requirements/REQ-PORT-vps-deploy.md).

---

## Prerequisites

| Requirement | Reference baseline | Where to get it |
|---|---|---|
| OS | Ubuntu 22.04 / 24.04 LTS or Debian 12 | provider's VPS image catalog |
| CPU | ≥ 4 vCPU | VPS plan |
| RAM | ≥ 8 GB | VPS plan |
| Disk | ≥ 50 GB | VPS plan |
| Docker Engine | ≥ 24 | https://docs.docker.com/engine/install/ |
| Docker Compose | v2 plugin (`docker compose` subcommand) | comes with modern Docker Engine |
| Outbound network | Docker Hub, ghcr.io, ollama.com | open by default on most VPSes |
| `git` | any recent | preinstalled on most VPSes |
| `openssl` | any recent (used to generate auth tokens) | preinstalled on most VPSes |

Lower-spec hardware may not meet the 60-minute target; the install will still succeed but `vision health` may report `degraded` while services warm up.

**Verify prereqs:**

```bash
docker --version                        # Docker version 24.x or higher
docker compose version                  # Compose version v2.x
free -h                                 # ≥ 8 GiB total
df -h /                                 # ≥ 50 GiB available on /
```

---

## Procedure

### Step 1: Clone the repo

```bash
git clone https://github.com/DYAI2025/Vision.git
cd Vision
```

### Step 2: Configure `.env`

```bash
cp .env.example .env
$EDITOR .env
```

**Required keys** (`install_vps.sh` will exit 1 if any are empty):

| Key | Value generation | Notes |
|---|---|---|
| `COMPOSE_PROFILES` | `caddy` (default) or `tailscale` | Caddy mode is the supported Phase-1 path. |
| `POSTGRES_PASSWORD` | `openssl rand -hex 32` | Database password. |
| `WHATSORGA_INGEST_TOKEN` | `openssl rand -hex 32` | Service auth token. |
| `HERMES_RUNTIME_TOKEN` | `openssl rand -hex 32` | Service auth token. |
| `BACKLOG_CORE_TOKEN` | `openssl rand -hex 32` | Service auth token. |
| `GBRAIN_BRIDGE_TOKEN` | `openssl rand -hex 32` | Service auth token. |
| `KANBAN_SYNC_TOKEN` | `openssl rand -hex 32` | Service auth token. |
| `OPERATOR_TOKEN` | `openssl rand -hex 32` | The CLI's identity to all services. |

**Tailscale-mode-only** (set when `COMPOSE_PROFILES=tailscale`):

| Key | Value generation | Notes |
|---|---|---|
| `TS_AUTHKEY` | https://login.tailscale.com/admin/settings/keys | Reusable + ephemeral recommended; tag with `tag:vision-ingress`. |
| `TS_HOSTNAME` | optional, defaults to `vision` | MagicDNS hostname. |

**Caddy public-deploy** (set when `CADDY_HOSTNAME` is not `localhost`):

| Key | Value | Notes |
|---|---|---|
| `CADDY_HOSTNAME` | e.g. `vision.example.com` | DNS must resolve to the VPS public IP before `docker compose up`. |
| `CADDY_ACME_EMAIL` | a real email | Let's Encrypt notifications. |

### Step 3: Run `install_vps.sh`

```bash
bash scripts/install_vps.sh
```

The script:
1. Verifies Docker + Compose v2.
2. Verifies `.env` is present and required keys are non-empty.
3. Runs `scripts/check-env-drift.sh` to confirm `.env.example` ↔ `docker-compose.yml` alignment.
4. `docker compose pull` (first-pass image pulls).
5. `docker compose build` (per-component images).
6. `docker compose up -d`.
7. Polls `docker inspect` for up to 5 minutes; expects all 7 containers (postgres, ollama, 5 backend services) to report `healthy`.
8. `scripts/ollama-pull.sh` to download the configured Gemma model (`OLLAMA_MODEL`, default `gemma3:4b`, ~3.3 GB).
9. Prints next steps.

**Expected exit codes:**

| Code | Meaning | Action |
|---|---|---|
| 0 | Install completed | Proceed to Step 4. |
| 1 | Prerequisite missing | Read the error message; install Docker / Compose / fill in `.env`; re-run. |
| 2 | Drift between `.env.example` and `docker-compose.yml` | Reconcile (the drift script names the offending keys). |
| 3 | Compose up succeeded but a service didn't become healthy | Inspect with `docker compose ps` and `docker compose logs --tail=200 <service>`. Stack is left running; re-run after fixing. |

The largest time consumer is the Ollama model pull (~3.3 GB). On a 100 Mbps link this is ~5 minutes. Image pulls (Postgres, Ollama base, Caddy, plus per-component build) account for another ~5-10 minutes on a fresh host.

### Step 4: Verify with `smoke_test.sh`

```bash
bash scripts/smoke_test.sh
```

The Phase-1 smoke test:
1. Verifies all 7 expected containers report Compose-`healthy`.
2. Invokes `vision health` via the in-stack `cli` Compose service.
3. Maps results to a stable exit-code contract.

**Expected exit codes:**

| Code | Meaning | Action |
|---|---|---|
| 0 | All containers healthy + `vision health` overall=ok | ✅ Phase-1 install verified. Proceed to Step 5. |
| 1 | Prerequisite missing | Re-run `install_vps.sh` first. |
| 2 | Container not Compose-healthy | `docker compose logs --tail=200 <container>`; common: Postgres still initializing, retry after 30s. |
| 3 | `vision health` returned `degraded` | At least one service reports a non-`ok` dependency. Inspect the per-service detail in the output. |
| 4 | `vision health` returned `down` | A service is unreachable. Likely network or container crash; check `docker compose ps` for restart loops. |
| 5 | Non-caddy `COMPOSE_PROFILES` | Smoke test does not currently support Tailscale mode. Run `vision health` directly from a tailnet-connected host (see "Tailscale-mode operator verification" below). |

### Step 5: Install or use the operator CLI

**Option A — install on the VPS host (recommended for laptop-style operation):**

```bash
# Install uv if not already present (one-time):
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
# Install the CLI:
uv tool install --from ./3-code/cli vision-cli
vision --version
vision health
```

After install, `vision` is on PATH globally. `vision health` reads `VISION_BASE_URL` and `OPERATOR_TOKEN` from the nearest upward `.env` (so running it from the repo root works without flags).

**Option B — invoke in-stack via the Compose `cli` service:**

```bash
docker compose --profile cli run --rm cli health
docker compose --profile cli run --rm cli health --json
```

Useful for one-off debugging without polluting the host's `uv tool install` registry.

---

## Manual verification scenarios (Phase 1)

Phase 1 is healthcheck-only. The functional smoke (synthetic ingest, routing, Kanban write, RTBF cascade) lands in Phase 7's `TASK-cross-provider-verification`. Until then, these are the manual scenarios to run after a fresh install:

### Scenario 1: All services healthy

```bash
bash scripts/smoke_test.sh
```

Expected: exit 0; output table shows 7 containers `healthy`; `vision health` overall=`ok`.

### Scenario 2: Backlog-Core 503 propagates correctly

Stop Postgres to verify the 503-on-degraded pattern works end-to-end:

```bash
docker compose stop postgres
sleep 5
docker compose --profile cli run --rm cli health --json | tee /tmp/health.json
docker compose start postgres
```

Expected: in the JSON, `services[].service == "backlog-core"` has `status: "degraded"` and `http_status: 503`. Overall=`degraded`. After Postgres restarts and the pool reconnects (~10s), `vision health` returns to `ok`.

### Scenario 3: gbrain-bridge missing-vault visibility

Simulate a misconfigured vault mount:

```bash
docker compose stop gbrain-bridge
docker compose rm -f gbrain-bridge
# Temporarily point gbrain-bridge at a nonexistent vault path:
VAULT_PATH=/does-not-exist docker compose up -d gbrain-bridge
sleep 5
docker compose --profile cli run --rm cli health
docker compose stop gbrain-bridge
docker compose up -d gbrain-bridge   # restore
```

Expected: gbrain-bridge reports `degraded` with `vault: down`. `install_vps.sh`'s healthcheck would fail in this state — by design, misconfiguration must be visible.

### Scenario 4: Operator CLI exit-code contract

```bash
vision health; echo "exit: $?"
```

Expected (when stack is healthy): exit code 0. Use this for shell-script gating: `if vision health; then ... fi` runs only when everything is `ok`.

### Tailscale-mode operator verification

Phase 1's `vision health` aggregator targets Caddy's `/v1/health/<service>` path-rewriting routes, which Tailscale serve does not support (no URL-rewrite primitive). The cli Compose service also hardcodes `VISION_BASE_URL=http://ingress-caddy`, so `docker compose --profile cli run --rm cli health` doesn't work in tailscale-only mode either. **Tailscale-only operators have two practical options:**

1. **Enable both ingresses** by setting `COMPOSE_PROFILES=caddy,tailscale` in `.env`. Caddy provides the aggregation paths over the Tailnet via the routes declared in `4-deploy/ingress/tailscale-serve.json`. This is the easiest path until tailscale-native aggregation lands.
2. **Wait for `TASK-tailscale-health-aggregation`** (see `3-code/tasks.md`, Phase 7), which adds either per-service health routes to `tailscale-serve.json` or a `--per-service` mode to `vision health` that bypasses Caddy aggregation.

Until then, in-stack `vision health` (Option B in Step 5 above) implicitly requires Caddy to be running.

---

## Troubleshooting

### `install_vps.sh` exits 1 — "Required .env keys are empty"

You have a `.env` but one or more required values is blank. The error message names the missing keys. Generate replacements:

```bash
echo "OPERATOR_TOKEN=$(openssl rand -hex 32)" >> .env
# (and so on for each missing key)
$EDITOR .env   # confirm and remove the now-duplicate empty key
```

### `install_vps.sh` exits 3 — "Not all services became healthy within 300s"

Most common cause: Postgres init takes longer than expected on a slow disk. Tail logs to confirm:

```bash
docker compose logs --tail=100 -f postgres
```

If you see `database system is ready to accept connections` followed by an immediate exit, suspect a corrupted volume — wipe with `docker compose down -v` (warning: drops all data) and re-run `install_vps.sh`.

If a backend service is unhealthy, check its logs:

```bash
docker compose logs --tail=200 backlog-core
docker compose logs --tail=200 hermes-runtime
# etc.
```

### `vision health` reports `down` for one service after install

Look at the JSON detail:

```bash
docker compose --profile cli run --rm cli health --json | jq '.services[] | select(.status != "ok")'
```

Then inspect that container's logs. A common pattern: container is healthy per Docker (`docker ps` shows `Up`) but its `/v1/health` endpoint reports `degraded` because a downstream is unreachable. The detail field tells you which downstream.

### Caddy can't get a certificate (public-hostname mode)

If you set `CADDY_HOSTNAME=vision.example.com` but the cert request fails:

```bash
docker compose logs --tail=100 ingress-caddy
```

Common causes:
- DNS hasn't propagated yet (wait 5-10 minutes after creating the A record).
- Port 80 is blocked at the firewall (Let's Encrypt's HTTP-01 challenge needs port 80).
- `CADDY_ACME_EMAIL` is empty or invalid.

### Tailscale node doesn't appear in admin

If `COMPOSE_PROFILES=tailscale` and the node doesn't show up in https://login.tailscale.com/admin/machines:

```bash
docker compose logs --tail=100 ingress-tailscale
```

Most common: `TS_AUTHKEY` is invalid, expired, or has been used past its limit (single-use keys exhaust on first registration). Generate a new reusable+ephemeral key from the admin console and update `.env`.

---

## Rollback / clean teardown

To stop the stack but preserve data:

```bash
docker compose down
```

To stop and **wipe all data** (Postgres database, Ollama models, GBrain vault, audit logs):

```bash
docker compose down -v
```

⚠️ **`-v` is destructive.** All volumes (`postgres-data`, `ollama-models`, `vault`, `caddy-data`, `caddy-config`, `tailscale-state`) are removed. Use only on a development host or after taking a backup (`scripts/backup.sh` lands with `TASK-backup-script` in Phase 7).

---

## Verifying the GDPR carry-over before any non-development deploy

Per `DEC-gdpr-legal-review-deferred`: production deployment is **blocked** until `ASM-derived-artifacts-gdpr-permissible.Status == Verified` in `1-spec/assumptions/`. This runbook is for **development / personal-use** deploys only. Before any deploy that:
- Registers a non-Vincent/Ben `actor_id` as a source, or
- Targets non-personal-use traffic,

complete the legal review, update the assumption file, and revisit this runbook with whatever delta the review surfaces (e.g., new consent-scope flag per the architecture's documented fallback).

---

## Other runbooks (lands with future phases)

- `4-deploy/runbooks/consent-and-audit.md` — `TASK-phase-2-manual-testing`
- `4-deploy/runbooks/ingest-end-to-end.md` — `TASK-phase-3-manual-testing`
- `4-deploy/runbooks/privacy.md` (RTBF, export, retention) — `TASK-phase-4-manual-testing`
- `4-deploy/runbooks/agent-and-kanban.md` — `TASK-phase-5-manual-testing`
- `4-deploy/runbooks/supervision-loop.md` — `TASK-phase-6-manual-testing`
- `4-deploy/runbooks/operability.md` (multi-channel, backup/restore, secret rotation, cross-provider) — `TASK-phase-7-manual-testing`
- `4-deploy/runbooks/secret-rotation.md` — `TASK-secret-rotation-runbook` (Phase 7)

---

## References

- Architecture: [`2-design/architecture.md`](../../2-design/architecture.md)
- API design: [`2-design/api-design.md`](../../2-design/api-design.md)
- Component READMEs: [`3-code/<component>/README.md`](../../3-code/) — build/run/test commands per component.
- Ingress reference: [`4-deploy/ingress/README.md`](../ingress/README.md)
- Postgres reference: [`4-deploy/postgres/README.md`](../postgres/README.md)
- Ollama reference: [`4-deploy/ollama/README.md`](../ollama/README.md)
- Scripts: [`scripts/`](../../scripts/) — `install_vps.sh`, `smoke_test.sh`, `check-env-drift.sh`, `ollama-pull.sh`, `ollama.sh`, `psql.sh`.
