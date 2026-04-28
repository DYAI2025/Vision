# Ingress

The system supports two ingress profiles, selected via `COMPOSE_PROFILES` in `.env`:

- **`caddy`** (default) — public-facing reverse proxy with auto-TLS via Let's Encrypt.
- **`tailscale`** — private-network-only ingress (configuration delivered by `TASK-ingress-tailscale-config`).

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

Configuration delivered by `TASK-ingress-tailscale-config` (next task in Phase 1). When that lands:

- A `tailscale serve` / `tailscale funnel` configuration script will live alongside this README.
- The Tailscale container's `command:` or post-up script will apply the configuration.
- Routing semantics will mirror the Caddy matrix above (path-based to internal services), but reachable only from the operator's Tailnet.

Until then, the `ingress-tailscale` service joins the Tailnet as a node but does not expose internal services.
