# Ingress

The system supports two ingress profiles, selected via `COMPOSE_PROFILES` in `.env`:

- **`caddy`** (default) — public-facing reverse proxy with auto-TLS via Let's Encrypt.
- **`tailscale`** — private-network-only ingress; reachable only from the operator's Tailnet.

This directory holds the configuration for both profiles.

## Caddy

Configuration: [`Caddyfile`](Caddyfile) — mounted read-only into the `ingress-caddy` container at `/etc/caddy/Caddyfile`.

### Required env vars

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `CADDY_HOSTNAME` | always | `localhost` | Public hostname or `localhost`. Determines auto-TLS behavior. |
| `CADDY_ACME_EMAIL` | when serving a non-`localhost` hostname | `operator@example.com` | Email registered with Let's Encrypt. |
| `CADDY_HTTP_PORT` | optional | `80` | Host port mapping for HTTP. |
| `CADDY_HTTPS_PORT` | optional | `443` | Host port mapping for HTTPS. |

For **local deployment**, `CADDY_HOSTNAME=localhost` is sufficient. Caddy's internal CA generates a self-signed cert on first request — operators trust it manually for `localhost` access.

For **public deployment** (e.g. `CADDY_HOSTNAME=vision.example.com`), Caddy requests a Let's Encrypt cert automatically on first start. Prerequisites:

- The hostname resolves to the VPS's public IP via DNS.
- Ports 80 and 443 are reachable from the public internet (firewall, port-forwarding, etc.).
- `CADDY_ACME_EMAIL` is set to a real email Let's Encrypt can contact.

### Routing matrix

Caddy routes by URL path, per `2-design/api-design.md`'s per-service namespaces:

| Path prefix | Routed to | Notes |
|---|---|---|
| `/v1/health/<service>` | `<service>` | Path rewritten to `/v1/health`; one of `backlog-core`, `whatsorga-ingest`, `hermes-runtime`, `gbrain-bridge`, `kanban-sync` |
| `/v1/inputs*`, `/v1/proposals*`, `/v1/sources*`, `/v1/rtbf*`, `/v1/exports*` | `backlog-core` | core API surface |
| `/v1/audit/*`, `/v1/state/*`, `/v1/sweep/*`, `/v1/reconciliation/*`, `/v1/review/*`, `/v1/events/*` | `backlog-core` | operator + agent endpoints |
| `/v1/pages*`, `/v1/audit-sweep*`, `/v1/dispositions` | `gbrain-bridge` | vault r/w + watch-script hook |
| `/v1/cards*`, `/v1/boards*`, `/v1/sync` | `kanban-sync` | kanban surface |
| `/v1/agent/*` | `hermes-runtime` | `POST /v1/agent/process-now` |
| `/` | 200 OK | static greeting |
| anything else | 404 | |

All upstream services listen on internal port 8000 on the Docker network. `/v1/audit/*` (backlog-core) does **not** collide with `/v1/audit-sweep*` (gbrain-bridge) — the boundary characters differ (`/` vs `-`).

### Updating routes

When new endpoints are added by future tasks:

1. Add the path to `Caddyfile` in the matching service block.
2. Document it in `2-design/api-design.md` (the design source of truth).
3. Update the routing matrix table above.
4. CI's `compose-validate` job will catch most mount-misconfigurations on the next push; for Caddy-syntax errors run `docker compose run --rm ingress-caddy caddy validate --config /etc/caddy/Caddyfile`.

## Tailscale

Configuration: [`tailscale-serve.json`](tailscale-serve.json) — mounted read-only into the `ingress-tailscale` container at `/config/serve.json`. Pointed to by the `TS_SERVE_CONFIG` environment variable; Tailscale's containerboot reads it once on start (image version ≥ 1.55) and applies it via `tailscale serve set`.

The Tailscale profile exposes the same path-based routing as Caddy, but only over the operator's Tailnet — no public exposure. `tailscale funnel` is **not** enabled (would conflict with `REQ-PORT-vps-deploy`'s private-network-only intent).

### Required env vars

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `TS_AUTHKEY` | always | — | Tailscale auth key. Get one at <https://login.tailscale.com/admin/settings/keys>. Use a reusable, ephemeral key for VPS-style deployments. |
| `TS_HOSTNAME` | optional | `vision` | MagicDNS hostname for this node. Reachable as `https://<TS_HOSTNAME>.<tailnet>.ts.net` once registered. |

### Operator setup (one-time)

1. **Create an auth key** in the Tailscale admin console. Tag the key (e.g. `tag:vision-ingress`) so an ACL rule can grant the right access; mark it ephemeral if the VPS is throwaway. Reusable=on, Ephemeral=on, Pre-approved=on (only if your tailnet requires device approval).
2. **Set `TS_AUTHKEY`** in `.env` (and `TS_HOSTNAME` if you want a name other than `vision`).
3. **Switch the profile**: `COMPOSE_PROFILES=tailscale` in `.env`.
4. **Bring up the stack**: `docker compose up -d`. The `ingress-tailscale` container starts, registers with the tailnet, requests a TLS cert (auto, MagicDNS-issued), and applies `tailscale-serve.json`.
5. **Verify** from another tailnet device: `curl https://vision.<your-tailnet>.ts.net/v1/health` (replace `vision` if you set a different `TS_HOSTNAME`). The cert validates without manual trust.

The reusable auth key only registers the node — it does not gate ongoing access. Tailnet ACLs gate which devices can reach the node.

### Routing matrix

Tailscale serve uses **longest-prefix matching**; declaration order in `tailscale-serve.json` is irrelevant. The matrix mirrors Caddy:

| Path prefix | Routed to | Notes |
|---|---|---|
| `/v1/inputs`, `/v1/proposals`, `/v1/sources`, `/v1/rtbf`, `/v1/exports` | `backlog-core` | core API surface |
| `/v1/audit/`, `/v1/state/`, `/v1/sweep/`, `/v1/reconciliation/`, `/v1/review/`, `/v1/events/` | `backlog-core` | operator + agent endpoints |
| `/v1/pages`, `/v1/audit-sweep`, `/v1/dispositions` | `gbrain-bridge` | vault r/w + watch-script hook |
| `/v1/cards`, `/v1/boards`, `/v1/sync` | `kanban-sync` | kanban surface |
| `/v1/agent/` | `hermes-runtime` | `POST /v1/agent/process-now` |

### Differences from the Caddy matrix

- **No path rewriting.** Tailscale's `serve` Handlers don't support URL rewrites, so the per-service `/v1/health/<service>` aggregation pattern from Caddy is not reproduced here. The full URL path is forwarded to the backend as-is. Operators in Tailscale mode use `vision health` (CLI) for aggregated health — the CLI is ingress-aware and polls each service directly when running over the Tailnet.
- **No `/` greeting or 404 fallback.** Tailscale serve only routes the prefixes declared in `tailscale-serve.json`; everything else returns Tailscale's default HTTP error (404 with the Tailscale identifier). This is acceptable — the Tailnet is operator-only, no anonymous browsing needed.
- **Trailing-slash discipline matters.** Tailscale uses prefix matching: `/v1/audit/` does **not** collide with `/v1/audit-sweep` because the latter has no trailing slash and is matched as a literal prefix. Keep this discipline when adding routes.

### Updating routes

When new endpoints are added by future tasks:

1. Add the path to `tailscale-serve.json` in the matching service block.
2. Add the same path to `Caddyfile` (so both ingress profiles stay in sync).
3. Document it in `2-design/api-design.md`.
4. Update both routing matrices in this README.
5. CI validates `Caddyfile` syntax on every push (see `.github/workflows/ci.yml#caddyfile-validate`); `tailscale-serve.json` is plain JSON — `python3 -m json.tool` confirms syntactic validity locally before commit.
