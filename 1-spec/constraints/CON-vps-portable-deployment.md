# CON-vps-portable-deployment: System runs on any VPS via Docker Compose, no host lock-in

**Category**: Technical

**Status**: Active

**Source stakeholder**: [STK-ben](../stakeholders.md)

## Description

The deployable unit must run on any VPS that supports Docker, without modification, given only the documented `.env` values. Specifically:

- All runtime configuration (hostnames, ports, paths, secret references, network topology choices) is provided via `.env` files consumed by `docker-compose.yml`.
- No hardcoded hostnames or IP addresses anywhere in code, Compose, or runbooks.
- No paths outside container-managed volumes — no `/home/<specific-user>/...`, no `/opt/<vendor-specific>`, no host-path side effects.
- No cloud-vendor-specific APIs (no AWS-only / GCP-only / Hetzner-only services as required dependencies). Optional integrations are allowed only if the system runs end-to-end without them.
- Tailscale is **recommended but optional**: the system must run end-to-end behind any reverse proxy (e.g., Caddy with a public hostname or behind Tailscale), with the choice driven by a single configuration item.

A "fresh VPS install" smoke test must complete on a vanilla Ubuntu/Debian VPS with only Docker, Docker Compose, and the repo cloned, using only `.env.example` filled in.

## Rationale

Avoids vendor lock-in (operational and commercial) and supports fast disaster recovery — Ben can rebuild on a different VPS in under an hour using only the repo + a backup. Matches the "VPS-of-the-day" posture: the deployment substrate is interchangeable, the system is not.

## Impact

- Constrains the Compose topology — service-to-service networking via internal Docker networks only; ingress via a single configurable reverse-proxy service.
- Drives an installation script (`install_vps.sh`) and a smoke-test script (`smoke_test.sh`) that run independently of any specific host.
- Drives a `REQ-PORT-vps-deploy` requirement (verifiable: smoke test passes on a fresh VPS).
- Drives a `REQ-MNT-env-driven-config` requirement (no source-code edits required to redeploy on a new host).
- Backup and restore procedures must produce/consume artifacts that are likewise host-independent (object-store-friendly archives, not host-bound paths).
